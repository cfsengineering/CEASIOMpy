
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
 
#ifndef GENUA_MEMFUN_H
#define GENUA_MEMFUN_H

/* ------------------------------------------------------------------------ */

template <class _Ret, class _Tp, class _Arg>
class ConstUnaryMemFunctor
{
  public:

    typedef _Arg argument_type;
    typedef _Ret result_type;

    explicit ConstUnaryMemFunctor( _Ret (_Tp::*_pf)(_Arg) const,
                                    const _Tp *_pt )  : _pobj(_pt), _Mf(_pf)
                                    {}

     _Ret operator() (_Arg a1) const
      { return (_pobj->*_Mf)(a1); }

  private:

    const _Tp *_pobj;
    _Ret (_Tp::*_Mf)(_Arg) const;
};

template <class _Ret, class _Tp, class _Arg>
class UnaryMemFunctor
{
  public:

    typedef _Arg argument_type;
    typedef _Ret result_type;

    explicit UnaryMemFunctor( _Ret (_Tp::*_pf)(_Arg),
                                    _Tp *_pt )  : _pobj(_pt), _Mf(_pf)   {}

    _Ret operator() (_Arg a1)
      { return (_pobj->*_Mf)(a1); }

  private:

    _Tp *_pobj;
    _Ret (_Tp::*_Mf)(_Arg);
};


template <class _Ret, class _Tp, class _Arg>
ConstUnaryMemFunctor<_Ret, _Tp, _Arg>
unMemFun(_Ret (_Tp::*_pf)(_Arg) const, const _Tp *_pt )
 {return ConstUnaryMemFunctor<_Ret, _Tp, _Arg>(_pf, _pt); }


template <class _Ret, class _Tp, class _Arg>
UnaryMemFunctor<_Ret, _Tp, _Arg>
unMemFun(_Ret (_Tp::*_pf)(_Arg), _Tp *_pt )
 {return UnaryMemFunctor<_Ret, _Tp, _Arg>(_pf, _pt); }


/* ------------------------------------------------------------------------ */

template <class _Ret, class _Tp, class _Arg1, class _Arg2>
class ConstBinaryMemFunctor
{
  public:

    typedef _Arg1 first_argument_type;
    typedef _Arg2 second_argument_type;
    typedef _Ret result_type;

    explicit ConstBinaryMemFunctor( _Ret (_Tp::*_pf)(_Arg1, _Arg2) const,
                                    const _Tp *_pt )  : _pobj(_pt), _Mf(_pf)
                                    {}

     _Ret operator() (_Arg1 a1, _Arg2 a2) const
      { return (_pobj->*_Mf)(a1,a2); }

  private:

    const _Tp *_pobj;
    _Ret (_Tp::*_Mf)(_Arg1, _Arg2) const;
};

template <class _Ret, class _Tp, class _Arg1, class _Arg2>
class BinaryMemFunctor
{
  public:

    typedef _Arg1 first_argument_type;
    typedef _Arg2 second_argument_type;
    typedef _Ret result_type;

    explicit BinaryMemFunctor( _Ret (_Tp::*_pf)(_Arg1, _Arg2),
                                    _Tp *_pt )  : _pobj(_pt), _Mf(_pf)   {}

    _Ret operator() (_Arg1 a1, _Arg2 a2)
      { return (_pobj->*_Mf)(a1,a2); }

  private:

    _Tp *_pobj;
    _Ret (_Tp::*_Mf)(_Arg1, _Arg2);
};


template <class _Ret, class _Tp, class _Arg1, class _Arg2>
ConstBinaryMemFunctor<_Ret, _Tp, _Arg1, _Arg2>
binMemFun(_Ret (_Tp::*_pf)(_Arg1, _Arg2) const, const _Tp *_pt )
 {return ConstBinaryMemFunctor<_Ret, _Tp, _Arg1, _Arg2>(_pf, _pt); }


template <class _Ret, class _Tp, class _Arg1, class _Arg2>
BinaryMemFunctor<_Ret, _Tp, _Arg1, _Arg2>
binMemFun(_Ret (_Tp::*_pf)(_Arg1, _Arg2), _Tp *_pt )
 {return BinaryMemFunctor<_Ret, _Tp, _Arg1, _Arg2>(_pf, _pt); }

#endif

