/* ------------------------------------------------------------------------
 * project:    Surf
 * file:       btree.h
 * begin:      Feb 2004
 * copyright:  (c) 2004 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * binary tree
 * ------------------------------------------------------------------------
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 * ------------------------------------------------------------------------ */

#ifndef _SURF_BTREE_H
#define _SURF_BTREE_H

#include <boost/shared_ptr.hpp>

class BinaryTree;
typedef boost::shared_ptr<BinaryTree> BinaryTreePtr;

class BinaryTree
{

  public:

	  /// empty constructor
		BinaryTree() : lft(0), rgt(0) {}

    /// access child node
		BinaryTree *left() const {return lft;}

    /// access child node
		BinaryTree *right() const {return rgt;}

  private:

	  /// left and right siblings
		BinaryTreePtr lft, rgt;
};

#endif

