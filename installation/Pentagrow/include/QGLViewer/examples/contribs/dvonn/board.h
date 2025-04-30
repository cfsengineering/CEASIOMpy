/****************************************************************************

 Copyright (C) 2002-2008 Gilles Debunne. All rights reserved.

 This file is part of the QGLViewer library version 2.3.1.

 http://www.libqglviewer.com - contact@libqglviewer.com

 This file may be used under the terms of the GNU General Public License 
 versions 2.0 or 3.0 as published by the Free Software Foundation and
 appearing in the LICENSE file included in the packaging of this file.
 In addition, as a special exception, Gilles Debunne gives you certain 
 additional rights, described in the file GPL_EXCEPTION in this package.

 libQGLViewer uses dual licensing. Commercial/proprietary software must
 purchase a libQGLViewer Commercial License.

 This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
 WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.

*****************************************************************************/

#ifndef DVONN_BOARD_H
#define DVONN_BOARD_H

#include <iostream>
#include <deque>
#include <string>
#include <vector>
#include <stack>
#include <map>

namespace dvonn
{
  const unsigned int nbColors = 3;
  typedef enum { Red=0, White=1, Black=2 } Color;
  const char* nameOf(const Color p);
 //++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
  // Interface of Piece
  //++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
  class Piece
  {
  public:
    Color color() const;
    bool isWhite() const;
    bool isBlack() const;
    bool isRed() const;
    bool is(Color c) const;
  protected:
    friend class Board;
    Piece(Color c);
  private:
    Color color_;
  };
  //++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
  // Interface of Stack
  //++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
  class Stack : public std::deque<const Piece*>
  {
  public:
    Stack();
    unsigned int height() const;
    bool hasPieces() const;
    const Piece* onTop() const;
    bool hasRed() const;
  protected:
    friend class Board;
  };
  //++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
  // Interface of Board
  //++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
  class Board
  {
  public:
    class Coord;
    static unsigned int nbSpacesMaxOnRow();
    static unsigned int nbRows();
    static bool isValid(Coord);
    static bool areAligned(Coord c0,Coord c1);
    static unsigned int distance(Coord c0,Coord c1);

    static unsigned int nbPieces(Color c);

    Board();
    void reinit();
    virtual ~Board();
    class ConstStackHandle;
    ConstStackHandle stackAt(Coord c) const;
    ConstStackHandle stackAt(int x,int y) const;
    class ConstStackIterator;
    ConstStackIterator stacks_begin() const;
    ConstStackIterator stacks_end() const;

    bool isFree(const ConstStackHandle& h) const;

    unsigned int nbUnplacedPieces(Color c) const;
    const Piece* getUnplacedPiece(Color c) const;
    void place(const Piece* p,Coord c);

    unsigned int heightMax() const;

    class Ghost;
    typedef std::deque<Ghost> Ghosts;
    Ghosts move(Coord src,Coord dst,bool killDeads);

    std::string prettyPrinted(const char* prefix="") const;
  private:
    Board& operator=(const Board&);
    Board(const Board&);
    friend class ConstStackHandle;
    friend class ConstStackIterator;
    static unsigned int coord2idx(Coord c);
    static Coord idx2coord(unsigned int);
    typedef std::pair<Stack,int> Space;
    std::vector<Space>           spaces_;
    std::deque<Piece>            pieces_;
    std::stack<const Piece*>     unplaced_[3];
    std::map<const Piece*,Coord> redSpaces_;

    void updateStatus(Ghosts& ghosts,bool killDeads);

  public:
    class State
    {
    private:
      friend class Board;
      std::vector<Space>           spaces_;
      std::stack<const Piece*>     unplaced_[3];
      std::map<const Piece*,Coord> redSpaces_;
    };
    State state() const;
    void restore(State);
  };
  //++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
  // Interface of Board::Coord
  //++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
  class Board::Coord
  {
  public:
    Coord(int x=-1,int y=-1);
    int x() const;
    int y() const;
    bool operator==(const Coord) const;
    bool operator!=(const Coord) const;
    bool operator<(const Coord) const;
  private:
    int x_;
    int y_;
  };
  //++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
  // Interface of Board::ConstStackHandle
  //++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
  class Board::ConstStackHandle
  {
  public:
    virtual ~ConstStackHandle();
    virtual operator bool() const;
    const Stack* operator->() const;
    const Stack& operator*() const;
    virtual bool operator==(const ConstStackHandle& other) const;
    virtual bool operator!=(const ConstStackHandle& other) const;
    Board::Coord stackCoord() const;
    int stackStatus() const;

    bool isNull() const;
    static ConstStackHandle null();
  protected:
    friend class Board;
    ConstStackHandle();
    ConstStackHandle(Coord c,const Space* s);
    void setCoord(Coord c);
    void setSpace(const Space*);
    const Space* space() const;
  private:
    Board::Coord coord_;
    const Space* space_;
  };
  //++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
  // Interface of Board::ConstStackIterator
  //++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
  class Board::ConstStackIterator : public Board::ConstStackHandle
  {
  public:
    virtual ~ConstStackIterator();
    virtual bool operator==(const ConstStackHandle& other) const;
    virtual bool operator!=(const ConstStackHandle& other) const;
    bool operator==(const ConstStackIterator& other) const;
    bool operator!=(const ConstStackIterator& other) const;
    ConstStackIterator& operator++();
  protected:
    friend class Board;
    ConstStackIterator();
    ConstStackIterator(Coord c,const Space* s,const Board* b);
  private:
    const Board* board_;
  };
  //++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
  // Interface of Board::Ghost
  //++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
  class Board::Ghost
  {
  public:
    Coord                    coord;
    std::deque<const Piece*> stack;
  protected:
    friend class Board;
    Ghost(Coord c,const Stack& s);
  };
};
extern std::ostream& operator<<(std::ostream&,const dvonn::Piece&);
extern std::ostream& operator<<(std::ostream&,const dvonn::Stack&);
extern std::ostream& operator<<(std::ostream&,const dvonn::Board::Coord);
extern std::ostream& operator<<(std::ostream&,const dvonn::Board::ConstStackHandle&);

#endif // DVONN_BOARD_H
