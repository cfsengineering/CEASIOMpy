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

#ifndef DVONN_GAME_H
#define DVONN_GAME_H

#include "board.h"
#include <qstring.h>
#include <vector>
#include <map>
#include <stdexcept>

namespace dvonn
{

  typedef enum { WhitePlayer=0, BlackPlayer=1 } Player;
  typedef enum { RedPlacementPhase  = 0,
		 PiecePlacementPhase= 1,
		 MovePhase          = 2,
		 GameOverPhase      = 3 } Phase;

  extern Color colorOf(Player p);
  extern Player player(Color c)/* throw (std::range_error)*/;
  extern QString nameOf(const dvonn::Player);
  //++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
  // Interface of Game
  //++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
  class Game
  {
  public:
    class Placement;
    class Move;

    Game();
    virtual ~Game();
    void reinit();

    const Board& board() const;

    Player theOnePlaying() const;
    Phase  phase() const;
    bool isOver() const;
    int score(Player) const;

    bool isLegalPlacement(const Placement) const;
    bool isLegalMove(const Move) const;

    bool doPlacement(const Placement);
    bool doMove(const Move);
    const Board::Ghosts* killedBy(const Move) const;
    std::deque<Board::ConstStackHandle> possibleDestinations(const Board::ConstStackHandle& h) const;

    void randomlyFinishPlacement();
    bool getRandomMove(Player p,Move& m) const;

    QString fileName() const;
    bool save();
    bool saveAs(const QString& fileName);
    bool load(const QString& fileName);

    void undo();
    void redo();
    bool canUndo() const;
    bool canRedo() const;
  private:
    void switchPlayers(Player p);
    void updateHistory();

    QString                              fileName_;
    Board                                board_;
    Phase                                phase_;
    Player                               player_;
    std::map<Move,Board::Ghosts>         ghosts_;
    int                                  score_[2];
    unsigned int                         time_;
    unsigned int                         knownTime_;
    std::deque<Board::State>             historyStates_;
    std::deque<Player>                   historyPlayers_;
    std::deque<Phase>                    historyPhases_;
  };
  //++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
  // Interface of Game::Placement
  //++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
  class Game::Placement
  {
  public:
    Placement(Color,Board::Coord);
    Color        color;
    Board::Coord dst;
  };
  //++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
  // Interface of Game::Move
  //++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
  class Game::Move
  {
  public:
    Move(Board::Coord = Board::Coord(),Board::Coord = Board::Coord());
    Board::Coord src;
    Board::Coord dst;
    bool operator<(const Move other) const;
  };
}
extern std::ostream& operator<<(std::ostream&,const dvonn::Game::Placement);
extern std::ostream& operator<<(std::ostream&,const dvonn::Game::Move);

#endif // DVONN_GAME_H
