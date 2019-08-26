//
//  transition_function.h
//
//  Created by Deepansh J. Srivastava, Apr 11, 2019
//  Copyright © 2019 Deepansh J. Srivastava. All rights reserved.
//  Contact email = srivastava.89@osu.edu, deepansh2012@gmail.com
//

#include "mrsimulator.h"

// Single nucleus spin transition functions................................. //

/**
 * @brief The @f$\mathbb{p}@f$ spin symmetry transition function.
 *
 * Single nucleus transition symmetry function from irreducible 1st-rank tensor,
 * given as
 * @f[
 *    \mathbb{p}(m_f, m_i) &= \left< m_f | \hat{T}_{10} | m_f \right> -
 *                            \left< m_i | \hat{T}_{10} | m_i \right> \\
 *                         &= m_f - m_i,
 * @f]
 * where @f$\hat{T}_{10}@f$ is the irreducible 1st rank spherical tensor
 * operator in the rotating tilted frame.
 *
 * @param mi The quantum number associated with the quantized initial energy
 *        level, @f$E_{m_i}@f$.
 * @param mf The quantum number associated with the quantized final energy
 *        level, @f$E_{m_f}@f$.
 * @returns The spin transition symmetry function @f$\mathbb{p}@f$.
 */
static inline double p(const double mf, const double mi) { return (mf - mi); }

/**
 * @brief The @f$\mathbb{d}@f$ spin transition symmetry function.
 *
 * Single nucleus transition symmetry function from irreducible 2nd-rank tensor,
 * given as
 * @f[
 *    \mathbb{d}(m_f, m_i) &= \left< m_f | \hat{T}_{20} | m_f \right> -
 *                            \left< m_i | \hat{T}_{20} | m_i \right> \\
 *    &= \sqrt{\frac{3}{2}} \left(m_f^2 - m_i^2 \right),
 * @f]
 * where @f$\hat{T}_{20}@f$ is the irreducible 2nd rank spherical tensor
 * operator in the rotating tilted frame.
 *
 * @param mi The quantum number associated with the quantized initial energy
 *        level, @f$E_{m_i}@f$.
 * @param mf The quantum number associated with the quantized final energy
 *        level, @f$E_{m_f}@f$.
 * @returns The spin transition symmetry function @f$\mathbb{d}@f$.
 */
static inline double d(const double mf, const double mi) {
  return 1.2247448714 * (mf * mf - mi * mi);
}

/**
 * @brief The @f$\mathbb{f}@f$ spin transition symmetry function.
 *
 * Single nucleus transition symmetry function from irreducible 3rd-rank tensor,
 * given as
 * @f[
 *    \mathbb{f}(m_f, m_i) &= \left< m_f | \hat{T}_{30} | m_f \right> -
 *                            \left< m_i | \hat{T}_{30} | m_i \right> \\
 *    &= \frac{1}{\sqrt{10}} [5(m_f^3 - m_i^3) + (1 - 3I(I+1))(m_f-m_i)],
 * @f]
 * where @f$\hat{T}_{30}@f$ is the irreducible 3rd rank spherical tensor
 * operator in the rotating tilted frame.
 *
 * @param mi The quantum number associated with the quantized initial energy
 *        level, @f$E_{m_i}@f$.
 * @param mf The quantum number associated with the quantized final energy
 *        level, @f$E_{m_f}@f$.
 * @return The spin transition symmetry function @f$\mathbb{f}@f$.
 */
static inline double f(const double mf, const double mi, const double spin) {
  double f_value = 1.0 - 3.0 * spin * (spin + 1.0);
  f_value *= (mf - mi);
  f_value += 5.0 * (mf * mf * mf - mi * mi * mi);
  f_value *= 0.316227766;
  return f_value;
}

/**
 * @brief The @f$\mathbb{c}_{L}@f$ spin transition symmetry functions.
 *
 * Single nucleus transition symmetry functions corresponding to the
 * @f$L=[0,2,4]@f$ rank irreducible tensors resulting from the second-order
 * corrections to the quadrupolar frequency. The functions are defined as
 * @f[
 *   \mathbb{c}_{0}(m_f, m_i) &= \frac{4}{\sqrt{125}} \left[I(I+1) -
 *          \frac{3}{4}\right] \mathbb{p}(m_f, m_i) +
 *          \sqrt{\frac{18}{25}} \mathbb{f}(m_f, m_i), \\
 *   \mathbb{c}_{2}(m_f, m_i) &= \sqrt{\frac{2}{175}} \left[I(I+1) -
 *          \frac{3}{4}\right] \mathbb{p}(m_f, m_i) -
 *          \frac{6}{\sqrt{35}} \mathbb{f}(m_f, m_i), \\
 *   \mathbb{c}_{4}(m_f, m_i) &= -\sqrt{\frac{18}{875}} \left[I(I+1) -
 *          \frac{3}{4}\right] \mathbb{p}(m_f, m_i) -
 *          \frac{17}{\sqrt{175}} \mathbb{f}(m_f, m_i),
 * @f]
 * where @f$\mathbb{p}(m_f, m_i)@f$ and @f$\mathbb{f}(m_f, m_i)@f$ are the
 * spin transition functions described before, and @f$I@f$ is the spin quantum
 * number.
 *
 * @param mi The quantum number associated with the quantized initial energy
 *        level, @f$E_{m_i}@f$.
 * @param mf The quantum number associated with the quantized final energy
 *        level, @f$E_{m_f}@f$.
 * @param spin The spin quantum number.
 * @param cl_value A pointer to an array of size 3 where the spin transition
 *        symmetry functions, @f$\mathbb{c}_{L}@f$ ordered according to
 *        @f$L=[0,2,4]@f$, will be stored.
 */
static inline void cL(double *restrict cl_value, const double mf,
                      const double mi, const double spin) {
  double f_value = f(mf, mi, spin);
  double p_value = p(mf, mi);
  double temp = spin * (spin + 1.0) - 0.75;
  temp *= p_value;

  *cl_value++ = 0.3577708764 * temp + 0.8485281374 * f_value;
  *cl_value++ = 0.1069044968 * temp + -1.0141851057 * f_value;
  *cl_value++ = -0.1434274331 * temp + -1.2850792082 * f_value;
}

// Two weakly coupled nuclei spin transition functions ..................... //

/**
 * @brief The @f$\mathbb{d}_{IS}@f$ spin transition symmetry function.
 *
 * Two weakly coupled nuclei transition symmetry function from the irreducible
 * 1st-rank tensors, defined as
 * @f[
 *   \mathbb{d}_{IS}(m_{If}, m_{Sf}, m_{Ii}, m_{Si}) &=
 *   \left<m_{If}m_{Sf}|\hat{T}_{10}(I)~\hat{T}_{10}(S)|m_{If} m_{Sf}\right>
 * -\left<m_{Ii}m_{Si}|\hat{T}_{10}(I)~\hat{T}_{10}(S)|m_{Ii} m_{Si}\right> \\
 *   &= m_{If} m_{Sf} - m_{Ii} m_{Si},
 * @f]
 * where @f$\hat{T}_{10}(I)@f$ and @f$\hat{T}_{10}(S)@f$ are the irreducible 1st
 * rank spherical tensor operators in the rotating tilted frame for spin I and
 * S, respectively.
 *
 * @param mIi The quantum number associated with the quantized initial energy
 *        level, @f$E_{{mI_i},{mS_i}}@f$ corresponding to spin I.
 * @param mSi The quantum number associated with the quantized initial energy
 *        level, @f$E_{{mI_i},{mS_i}}@f$ corresponding to spin S.
 * @param mIf The quantum number associated with the quantized final energy
 *        level, @f$E_{{mI_f},{mS_f}}@f$ corresponding to spin I.
 * @param mSf The quantum number associated with the quantized final energy
 *        level, @f$E_{{mI_f},{mS_f}}@f$ corresponding to spin S.
 * @return The spin transition symmetry function @f$\mathbb{d}_{IS}@f$.
 */
static inline double dIS(const double mIf, const double mIi, const double mSf,
                         const double mSi) {
  return mIf * mSf - mIi * mSi;
}
