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

#include <fstream>
#include <stdio.h>
#include "board.h"

int main (int argc, char ** argv)
{    
  if (argc != 4) {
	  std::cout << "This AI agora player requires 3 parameters. It should be called by the main agora viewer application." << std::endl;
	  exit(1);
  }
  
  Board board;

  std::ifstream file(argv[1]);
  file >> board;
  file.close();

  std::cout << board.randomMove(QString(argv[2]).toInt()>=0) << std::endl;

  return 0;
}
