
/* Copyright (C) 2015 David Eller <david@larosterna.com>
 * 
 * Commercial License Usage
 * Licensees holding valid commercial licenses may use this file in accordance
 * with the terms contained in their respective non-exclusive license agreement.
 * For further information contact david@larosterna.com .
 *
 * GNU General Public License Usage
 * Alternatively, this file may be used under the terms of the GNU General
 * Public License version 3.0 as published by the Free Software Foundation and
 * appearing in the file gpl.txt included in the packaging of this file.
 */
 
#ifndef OMP_FORWARD_H
#define OMP_FORWARD_H

/** \file omp_forward.h
 *  \brief Forward declarations for OpenMP functions.
 *
 * This file can be used to expose the declarations of the most important
 * OpenMP runtime interface functions on systems where the "omp.h" header is
 * missing but the libraries are present.
 *
 * \ingroup utility
 *
 */

#ifdef __cplusplus
extern "C" {
#endif

typedef enum omp_sched_t {
  omp_sched_static  = 1,
  omp_sched_dynamic = 2,
  omp_sched_guided  = 3,
  omp_sched_auto    = 4
} omp_sched_t;

extern void omp_set_num_threads(int);
extern void omp_set_dynamic(int);
extern void omp_set_nested(int);
extern void omp_set_max_active_levels(int);
extern void omp_set_schedule(omp_sched_t, int);

extern int omp_get_num_threads(void);
extern int omp_get_dynamic(void);
extern int omp_get_nested(void);
extern int omp_get_max_threads(void);
extern int omp_get_thread_num(void);
extern int omp_get_num_procs(void);
extern int omp_in_parallel(void);
extern int omp_get_active_level(void);
extern int omp_get_level(void);
extern int omp_get_ancestor_thread_num(int);
extern int omp_get_team_size(int);
extern int omp_get_thread_limit(void);
extern int omp_get_max_active_levels(void);
extern void omp_get_schedule(omp_sched_t *, int *);

typedef struct omp_lock_t omp_lock_t;

extern void omp_init_lock(omp_lock_t *);
extern void omp_set_lock(omp_lock_t *);
extern void omp_unset_lock(omp_lock_t *);
extern void omp_destroy_lock(omp_lock_t *);
extern int  omp_test_lock(omp_lock_t *);

typedef struct omp_nest_lock_t omp_nest_lock_t;

extern void omp_init_nest_lock(omp_nest_lock_t *);
extern void omp_set_nest_lock(omp_nest_lock_t *);
extern void omp_unset_nest_lock(omp_nest_lock_t *);
extern void omp_destroy_nest_lock(omp_nest_lock_t *);
extern int  omp_test_nest_lock(omp_nest_lock_t *);

extern double omp_get_wtime(void);
extern double omp_get_wtick(void);

#ifdef __cplusplus
}
#endif

#endif // OMP_FORWARD_H
