
#include "umfpacksolver.h"
#include "umfpack.h"
#include "configparser.h"

UmfpackContext::UmfpackContext(bool useComplex)
  : CholmodContext(), m_iscomplex(useComplex)
{
  assert(UMFPACK_CONTROL <= 128);
  assert(UMFPACK_INFO <= 128);
  if (not m_iscomplex)
    umfpack_dl_defaults(m_control);
  else
    umfpack_zl_defaults(m_control);
}

UmfpackContext::~UmfpackContext()
{
  release();
}

void UmfpackContext::configure(const ConfigParser &cfg)
{
  CholmodContext::configure(cfg);
  m_control[UMFPACK_DROPTOL] = cfg.getFloat("DropTolerance", 0.0);
  if (cfg.hasKey("MatrixOrdering")) {
    std::string s = toLower(cfg["MatrixOrdering"]);
    if (s == "natural")
      m_control[UMFPACK_ORDERING] = UMFPACK_ORDERING_GIVEN;
    else if (s == "cholmod")
      m_control[UMFPACK_ORDERING] = UMFPACK_ORDERING_CHOLMOD;
    else if (s == "amd")
      m_control[UMFPACK_ORDERING] = UMFPACK_ORDERING_AMD;
    else if (s == "metis")
      m_control[UMFPACK_ORDERING] = UMFPACK_ORDERING_METIS;
    else if (s == "best")
      m_control[UMFPACK_ORDERING] = UMFPACK_ORDERING_BEST;
    else if (s == "bestamd")
      m_control[UMFPACK_ORDERING] = UMFPACK_ORDERING_BEST;
    else
      m_control[UMFPACK_ORDERING] = UMFPACK_ORDERING_BEST;
  } else {
    m_control[UMFPACK_ORDERING] = UMFPACK_ORDERING_BEST;
  }
}

bool UmfpackContext::factorizeSymbolic()
{
  if (m_psymbolic != nullptr) {
    if (not m_iscomplex)
      umfpack_dl_free_symbolic(&m_psymbolic);
    else
      umfpack_zl_free_symbolic(&m_psymbolic);
  }

  index_t m = m_psparse->nrow;
  index_t n = m_psparse->ncol;
  const index_t *Ap = reinterpret_cast<const index_t *>( m_psparse->p );
  const index_t *Ai = reinterpret_cast<const index_t *>( m_psparse->i );
  const double *Ax = reinterpret_cast<const double *>( m_psparse->x );

  if (not m_iscomplex)
    umfpack_dl_symbolic(m, n, Ap, Ai, Ax, &m_psymbolic, m_control, m_info);
  else
    umfpack_zl_symbolic(m, n, Ap, Ai, Ax, nullptr,
                        &m_psymbolic, m_control, m_info);

  return (m_info[UMFPACK_STATUS] >= 0);
}

bool UmfpackContext::factorizeNumeric()
{
  assert(m_psymbolic != nullptr);
  if (m_pnumeric != nullptr) {
    if (not m_iscomplex)
      umfpack_dl_free_numeric(&m_pnumeric);
    else
      umfpack_zl_free_numeric(&m_pnumeric);
  }

  const index_t *Ap = reinterpret_cast<const index_t *>( m_psparse->p );
  const index_t *Ai = reinterpret_cast<const index_t *>( m_psparse->i );
  const double *Ax = reinterpret_cast<const double *>( m_psparse->x );

  if (not m_iscomplex)
    umfpack_dl_numeric(Ap, Ai, Ax, m_psymbolic, &m_pnumeric,
                       m_control, m_info);
  else
    umfpack_zl_numeric(Ap, Ai, Ax, nullptr, m_psymbolic, &m_pnumeric,
                       m_control, m_info);

  return (m_info[UMFPACK_STATUS] >= 0);
}

bool UmfpackContext::solve(bool transposed, const double b[], double x[])
{
  assert(m_pnumeric != nullptr);
  index_t sys = transposed ? UMFPACK_At : UMFPACK_A;
  const index_t *Ap = reinterpret_cast<const index_t *>( m_psparse->p );
  const index_t *Ai = reinterpret_cast<const index_t *>( m_psparse->i );
  const double *Ax = reinterpret_cast<const double *>( m_psparse->x );
  index_t stat;
  stat = umfpack_dl_solve(sys, Ap, Ai, Ax, x, b, m_pnumeric, m_control, m_info) ;
  return (stat == UMFPACK_OK);
}

bool UmfpackContext::solve(bool transposed,
                           const std::complex<double> b[],
                           std::complex<double> x[])
{
  assert(m_pnumeric != nullptr);
  index_t sys = transposed ? UMFPACK_At : UMFPACK_A;
  // int m = m_psparse->nrow;
  const index_t *Ap = reinterpret_cast<const index_t *>( m_psparse->p );
  const index_t *Ai = reinterpret_cast<const index_t *>( m_psparse->i );
  const double *Ax = reinterpret_cast<const double *>( m_psparse->x );
  const double *pb = reinterpret_cast<const double *>( b );
  double *px = reinterpret_cast<double *>( x );
  index_t stat;
  stat = umfpack_zl_solve(sys, Ap, Ai, Ax, nullptr, px, nullptr, pb, nullptr,
                          m_pnumeric, m_control, m_info) ;
  return (stat == UMFPACK_OK);
}

double UmfpackContext::peakMemory() const
{
  if (m_pnumeric != nullptr)
    return m_info[UMFPACK_PEAK_MEMORY];
  else if (m_psymbolic != nullptr)
    return m_info[UMFPACK_PEAK_MEMORY_ESTIMATE];

  return 0.0;
}

void UmfpackContext::release()
{
  if (m_psymbolic != nullptr) {
    if (not m_iscomplex)
      umfpack_dl_free_symbolic(&m_psymbolic);
    else
      umfpack_zl_free_symbolic(&m_psymbolic);
  }
  m_psymbolic = nullptr;

  if (m_pnumeric != nullptr) {
    if (not m_iscomplex)
      umfpack_dl_free_numeric(&m_pnumeric);
    else
      umfpack_zl_free_numeric(&m_pnumeric);
  }
  m_pnumeric = nullptr;

  CholmodContext::release();
}

const char *UmfpackContext::lastMessage() const
{
  static const char *msg[] = {"UMFPACK: All is well.",           // 0
                              "UMFPACK: Negative matrix size.",  // 1
                              "UMFPACK: Invalid matrix.",        // 2
                              "UMFPACK: Out of memory.",         // 3
                              "UMFPACK: Argument missing.",      // 4
                              "UMFPACK: Invalid symbolic object.",      // 5
                              "UMFPACK: Matrix pattern is different.",  // 6
                              "UMFPACK: Invalid permutation.",   // 7
                              "UMFPACK: Invalid numeric object.",      // 8
                              "UMFPACK: Invalid linear system.",      // 9
                              "UMFPACK: Internal error."};            // 10

  if ( m_info[UMFPACK_STATUS] == UMFPACK_OK )
    return msg[0];
  else if ( m_info[UMFPACK_STATUS] == UMFPACK_ERROR_n_nonpositive )
    return msg[1];
  else if ( m_info[UMFPACK_STATUS] == UMFPACK_ERROR_invalid_matrix )
    return msg[2];
  else if ( m_info[UMFPACK_STATUS] == UMFPACK_ERROR_out_of_memory )
    return msg[3];
  else if ( m_info[UMFPACK_STATUS] == UMFPACK_ERROR_argument_missing )
    return msg[4];
  else if ( m_info[UMFPACK_STATUS] == UMFPACK_ERROR_invalid_Symbolic_object )
    return msg[5];
  else if ( m_info[UMFPACK_STATUS] == UMFPACK_ERROR_different_pattern )
    return msg[6];
  else if ( m_info[UMFPACK_STATUS] == UMFPACK_ERROR_invalid_permutation )
    return msg[7];
  else if ( m_info[UMFPACK_STATUS] == UMFPACK_ERROR_invalid_Numeric_object )
    return msg[8];
  else if ( m_info[UMFPACK_STATUS] == UMFPACK_ERROR_invalid_system )
    return msg[9];
  else if ( m_info[UMFPACK_STATUS] == UMFPACK_ERROR_internal_error )
    return msg[10];

  return "UMFPACK: Unknown error code";
}


