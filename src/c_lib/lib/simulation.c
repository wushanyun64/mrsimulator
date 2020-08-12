// -*- coding: utf-8 -*-
//
//  sideband_simulator.c
//
//  @copyright Deepansh J. Srivastava, 2019-2020.
//  Created by Deepansh J. Srivastava, Apr 11, 2019
//  Contact email = deepansh2012@gmail.com
//

#include "simulation.h"

static inline void __zero_components(double *R0, complex128 *R2,
                                     complex128 *R4) {
  R0[0] = 0.0;
  vm_double_zeros(10, (double *)R2);
  vm_double_zeros(18, (double *)R4);
}

void __mrsimulator_core(
    // spectrum information and related amplitude
    double *spec,  // amplitude vector representing the spectrum.

    // A pointer to the isotopomer_ravel structure containing information about
    // the sites within an isotopomer.
    isotopomer_ravel *ravel_isotopomer,

    // remove the isotropic contribution from the second order quad Hamiltonian.
    bool remove_2nd_order_quad_isotropic,

    // A pointer to a spin transition packed as quantum numbers from the initial
    // energy state followed by the quantum numbers from the final energy state.
    // The energy states are given in Zeeman basis.
    float *transition,

    // A pointer to MRS_sequence structure containing information on the events
    // per spectroscopic dimension.
    MRS_sequence *the_sequence,

    // The total number of spectroscopic dimensions.
    int n_sequence,

    // A pointer to the fftw scheme.
    MRS_fftw_scheme *fftw_scheme,

    // A pointer to the powder averaging scheme.
    MRS_averaging_scheme *scheme,

    // if true, perform a 1D interpolation
    bool interpolation) {
  /*
  The sideband computation is based on the method described by Eden and Levitt
  et. al. `Computation of Orientational Averages in Solid-State NMR by Gaussian
  Spherical Quadrature` JMR, 132, 1998. https://doi.org/10.1006/jmre.1998.1427
  */
  bool refresh;
  unsigned int evt;
  int seq;
  double B0_in_T;

  double R0 = 0.0;
  complex128 *R2 = malloc_complex128(5);
  complex128 *R4 = malloc_complex128(9);

  double R0_temp = 0.0;
  complex128 *R2_temp = malloc_complex128(5);
  complex128 *R4_temp = malloc_complex128(9);
  double *spec_site_ptr;
  int transition_increment = 2 * ravel_isotopomer->number_of_sites;
  MRS_plan *plan;
  MRS_event *event;

  // spec_site = site * the_sequence[0].count;
  spec_site_ptr = &spec[0];

  // Loop over the sequence.
  for (seq = 0; seq < n_sequence; seq++) {
    refresh = 1;
    // Loop over the events per sequence.
    for (evt = 0; evt < the_sequence[seq].n_events; evt++) {
      event = &the_sequence[seq].events[evt];
      plan = event->plan;
      B0_in_T = event->magnetic_flux_density_in_T;

      /* Initialize with zeroing all spatial components */
      __zero_components(&R0, R2, R4);

      /* Rotate all frequency components from PAS to a common frame */
      MRS_rotate_components_from_PAS_to_common_frame(
          ravel_isotopomer,         // isotopomer structure
          transition,               // the transition
          plan->allow_fourth_rank,  // if 1, prepare for 4th rank computation
          &R0,                      // the R0 components
          R2,                       // the R2 components
          R4,                       // the R4 components
          &R0_temp,                 // the temporary R0 components
          R2_temp,                  // the temporary R2 components
          R4_temp,                  // the temporary R4 components
          remove_2nd_order_quad_isotropic,  // if true, remove second order quad
                                            // isotropic shift
          B0_in_T                           // magnetic flux density in T.
      );

      // Add a loop over all couplings.. here
      /* Get frequencies and amplitudes per octant .........................
       */
      /* Always evalute the frequencies before the amplitudes. */
      MRS_get_normalized_frequencies_from_plan(scheme, plan, R0, R2, R4,
                                               refresh, &the_sequence[seq]);
      MRS_get_amplitudes_from_plan(scheme, plan, fftw_scheme, 1);
      if (plan->number_of_sidebands != 1) {
        cblas_dcopy(plan->size, (double *)fftw_scheme->vector, 2,
                    event->freq_amplitude, 1);
      }
      transition += transition_increment;
      refresh = 0;
    }  // end events
  }    // end sequences

  /* If the number of sidebands is 1, the sideband amplitude at every sideband
   * order is one. In this case, update the `fftw_scheme->vector` is the same as
   * the weights from the orientation averaging,
   */
  // if (plan->number_of_sidebands == 1) {
  //   /* Scaling the absolute value square with the powder scheme weights. Only
  //    * the real part is scaled and the imaginary part is left as is.
  //    */
  //   for (i = 0; i < plan->n_octants; i++) {
  //     cblas_dcopy(scheme->octant_orientations, plan->norm_amplitudes, 1,
  //                 &the_sequence[0]
  //                      .events[0]
  //                      .freq_amplitude[i * scheme->octant_orientations],
  //                 1);
  //   }
  // } else {
  //   /* Scaling the absolute value square with the powder scheme weights. Only
  //    * the real part is scaled and the imaginary part is left as is.
  //    */
  //   for (i = 0; i < scheme->octant_orientations; i++) {
  //     cblas_dscal(plan->n_octants * plan->number_of_sidebands,
  //                 plan->norm_amplitudes[i],
  //                 &the_sequence[0].events[0].freq_amplitude[i],
  //                 scheme->octant_orientations);
  //   }
  // }

  /* ---------------------------------------------------------------------
   *              Calculating the tent for every sideband
   * Allowing only sidebands that are within the spectral bandwidth
   *
   * for (i = 0; i < plan->number_of_sidebands; i++) {
   *   offset = plan->vr_freq[i] + plan->isotropic_offset;
   *   if ((int)offset >= 0 && (int)offset <= dimension->count) {

   *     vm_double_ramp(plan->octant_orientations,
   plan->local_frequency, 1.0,
   *                    offset, plan->freq_offset);
   *     octahedronInterpolation(
   *         spec_site_ptr, plan->freq_offset,
   *         plan->integration_density,
   *         (double *)&plan->vector[i * plan->octant_orientations], 2,
   *         dimension->count);
   *   }
   * }
   */
  if (interpolation) {
    if (n_sequence == 1) {
      one_dimensional_averaging(the_sequence, scheme, fftw_scheme, spec,
                                plan->number_of_sidebands);
    }

    if (n_sequence == 2) {
      two_dimensional_averaging(the_sequence, scheme, fftw_scheme, spec,
                                plan->number_of_sidebands);
    }
  }

  // gettimeofday(&end_site_time, NULL);
  // clock_time =
  //     (double)(end_site_time.tv_usec - start_site_time.tv_usec) /
  //     1000000.
  //     + (double)(end_site_time.tv_sec - start_site_time.tv_sec);
  // printf("Total time per site %f \n", clock_time);
}

void mrsimulator_core(
    // spectrum information and related amplitude
    double *spec,               // The amplitude of the spectrum.
    double coordinates_offset,  // The start of the frequency spectrum.
    double increment,           // The increment of the frequency spectrum.
    int count,                  // Number of points on the frequency spectrum.
    isotopomer_ravel *ravel_isotopomer,    // SpinSystem structure
    MRS_sequence *the_sequence,            // the sequences in the method.
    int n_sequence,                        // The number of sequence.
    int quad_second_order,                 // Quad theory for second order,
    bool remove_2nd_order_quad_isotropic,  // remove the isotropic
                                           // contribution from the second
                                           // order quad interaction.

    // spin rate, spin angle and number spinning sidebands
    int number_of_sidebands,                 // The number of sidebands
    double sample_rotation_frequency_in_Hz,  // The rotor spin frequency
    double rotor_angle_in_rad,  // The rotor angle relative to lab-frame z-axis

    // Pointer to the transitions. transition[0] = mi and transition[1] = mf
    float *transition,

    // powder orientation average
    int integration_density,          // The number of triangle along the edge
                                      // of octahedron
    unsigned int integration_volume,  // 0-octant, 1-hemisphere, 2-sphere.
    bool interpolation) {
  // int num_process = openblas_get_num_procs();
  // int num_threads = openblas_get_num_threads();
  // // openblas_set_num_threads(1);
  // printf("%d processors", num_process);
  // printf("%d threads", num_threads);
  // int parallel = openblas_get_parallel();
  // printf("%d parallel", parallel);

  bool allow_fourth_rank = false;
  if (ravel_isotopomer[0].spin[0] > 0.5 && quad_second_order == 1) {
    allow_fourth_rank = true;
  }

  // check for spinning speed
  if (sample_rotation_frequency_in_Hz < 1.0e-3) {
    sample_rotation_frequency_in_Hz = 1.0e9;
    rotor_angle_in_rad = 0.0;
    number_of_sidebands = 1;
  }

  MRS_averaging_scheme *scheme = MRS_create_averaging_scheme(
      integration_density, allow_fourth_rank, integration_volume);

  MRS_fftw_scheme *fftw_scheme =
      create_fftw_scheme(scheme->total_orientations, number_of_sidebands);

  // gettimeofday(&all_site_time, NULL);
  __mrsimulator_core(
      // spectrum information and related amplitude
      spec,  // The amplitude of the spectrum.

      ravel_isotopomer,  // isotopomer structure

      remove_2nd_order_quad_isotropic,  // remove the isotropic contribution
                                        // from the second order quad
                                        // Hamiltonian.

      // Pointer to the transitions. transition[0] = mi and transition[1] = mf
      transition,

      the_sequence, n_sequence, fftw_scheme, scheme, interpolation);

  // gettimeofday(&end, NULL);
  // clock_time = (double)(end.tv_usec - begin.tv_usec) / 1000000. +
  //              (double)(end.tv_sec - begin.tv_sec);
  // printf("time %f s\n", clock_time);
  // cpu_time_[0] += clock_time;

  /* clean up */
  MRS_free_fftw_scheme(fftw_scheme);
  MRS_free_averaging_scheme(scheme);
  // MRS_free_plan(plan);
}

void one_dimensional_averaging(MRS_sequence *the_sequence,
                               MRS_averaging_scheme *scheme,
                               MRS_fftw_scheme *fftw_scheme, double *spec,
                               int number_of_sidebands) {
  unsigned int i, j, evt, step_vector = 0, address;
  MRS_plan *plan;
  MRS_event *event;
  int size = scheme->total_orientations * number_of_sidebands;
  double *freq_amp = malloc_double(size);
  double offset, offset1;

  vm_double_ones(size, freq_amp);

  // offset = plan->vr_freq[i] + plan->isotropic_offset +
  //          the_sequence[seq].normalize_offset;
  offset = the_sequence[0].normalize_offset + the_sequence[0].R0_offset;
  for (evt = 0; evt < the_sequence[0].n_events; evt++) {
    event = &the_sequence[0].events[evt];
    plan = event->plan;
    // offset += plan->R0_offset;
    vm_double_multiply_inplace(size, event->freq_amplitude, 1, freq_amp, 1);
  }

  for (j = 0; j < scheme->octant_orientations; j++) {
    cblas_dscal(plan->n_octants * number_of_sidebands, plan->norm_amplitudes[j],
                &freq_amp[j], scheme->octant_orientations);
  }

  for (i = 0; i < number_of_sidebands; i++) {
    offset1 = offset + plan->vr_freq[i];
    if ((int)offset1 >= 0 && (int)offset1 <= the_sequence[0].count) {
      step_vector = i * scheme->total_orientations;
      for (j = 0; j < plan->n_octants; j++) {
        address = j * scheme->octant_orientations;
        // Add offset(isotropic + sideband_order) to the local frequency
        // from [n to n+octant_orientation]
        vm_double_ramp(scheme->octant_orientations,
                       &the_sequence[0].local_frequency[address], 1.0, offset1,
                       the_sequence[0].freq_offset);
        // Perform tenting on every sideband order over all orientations
        octahedronInterpolation(
            spec, the_sequence[0].freq_offset, scheme->integration_density,
            &freq_amp[step_vector], 1, the_sequence[0].count);
        step_vector += scheme->octant_orientations;
      }
    }
  }
  free(freq_amp);
}

void two_dimensional_averaging(MRS_sequence *the_sequence,
                               MRS_averaging_scheme *scheme,
                               MRS_fftw_scheme *fftw_scheme, double *spec,
                               int number_of_sidebands) {
  unsigned int i, j, k, evt;
  unsigned int step_vector_i = 0, step_vector_k = 0, address;
  MRS_plan *plan;
  MRS_event *event;
  int size = scheme->total_orientations * number_of_sidebands;
  double *freq_ampA = malloc_double(size);
  double *freq_ampB = malloc_double(size);
  double *freq_amp = malloc_double(scheme->total_orientations);
  double offset0, offset1, offsetA, offsetB;

  vm_double_ones(size, freq_ampA);
  vm_double_ones(size, freq_ampB);

  // offset = plan->vr_freq[i] + plan->isotropic_offset +
  //          the_sequence[seq].normalize_offset;
  offset0 = the_sequence[0].normalize_offset + the_sequence[0].R0_offset;
  for (evt = 0; evt < the_sequence[0].n_events; evt++) {
    event = &the_sequence[0].events[evt];
    plan = event->plan;
    // offset0 += plan->R0_offset;
    vm_double_multiply_inplace(size, event->freq_amplitude, 1, freq_ampA, 1);
  }

  offset1 = the_sequence[1].normalize_offset + the_sequence[1].R0_offset;
  for (evt = 0; evt < the_sequence[1].n_events; evt++) {
    event = &the_sequence[1].events[evt];
    plan = event->plan;
    // offset1 += plan->R0_offset;
    vm_double_multiply_inplace(size, event->freq_amplitude, 1, freq_ampB, 1);
  }

  for (j = 0; j < scheme->octant_orientations; j++) {
    cblas_dscal(plan->n_octants * number_of_sidebands, plan->norm_amplitudes[j],
                &freq_ampB[j], scheme->octant_orientations);
  }

  for (i = 0; i < number_of_sidebands; i++) {
    offsetA = offset0 + plan->vr_freq[i];
    if ((int)offsetA >= 0 && (int)offsetA <= the_sequence[0].count) {
      step_vector_i = i * scheme->total_orientations;
      for (k = 0; k < number_of_sidebands; k++) {
        offsetB = offset1 + plan->vr_freq[k];
        if ((int)offsetB >= 0 && (int)offsetB <= the_sequence[1].count) {
          step_vector_k = k * scheme->total_orientations;

          // step_vector = 0;
          for (j = 0; j < plan->n_octants; j++) {
            address = j * scheme->octant_orientations;
            // Add offset(isotropic + sideband_order) to the local frequency
            // from [n to n+octant_orientation]
            vm_double_ramp(scheme->octant_orientations,
                           &the_sequence[0].local_frequency[address], 1.0,
                           offsetA, the_sequence[0].freq_offset);
            vm_double_ramp(scheme->octant_orientations,
                           &the_sequence[1].local_frequency[address], 1.0,
                           offsetB, the_sequence[1].freq_offset);

            vm_double_multiply(scheme->total_orientations,
                               &freq_ampA[step_vector_i + address],
                               &freq_ampB[step_vector_k + address], freq_amp);
            // Perform tenting on every sideband order over all orientations
            octahedronInterpolation2D(
                spec, the_sequence[0].freq_offset, the_sequence[1].freq_offset,
                scheme->integration_density, freq_amp, 1, the_sequence[0].count,
                the_sequence[1].count);
            // step_vector += scheme->octant_orientations;
          }
        }
      }
    }
  }
  free(freq_amp);
  free(freq_ampA);
  free(freq_ampB);
}
