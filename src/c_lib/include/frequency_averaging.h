// -*- coding: utf-8 -*-
//
//  frequency_averaging.h
//
//  @copyright Deepansh J. Srivastava, 2019-2021.
//  Created by Deepansh J. Srivastava, Mar 2, 2021.
//  Contact email = srivastava.89@osu.edu
//

#include "simulation.h"

void one_dimensional_averaging(MRS_dimension *dimensions, MRS_averaging_scheme *scheme,
                               double *spec, double transition_pathway_weight,
                               unsigned int iso_intrp);

void two_dimensional_averaging(MRS_dimension *dimensions, MRS_averaging_scheme *scheme,
                               double *spec, double transition_pathway_weight,
                               double *affine_matrix, unsigned int iso_intrp);
