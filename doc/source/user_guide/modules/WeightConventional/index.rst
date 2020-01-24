WeightConventional
==================

# TODO be sure it is compile correctly

Weight conventional module for preliminary design of conventional aircraft evaluates:

 * the maximum take-off mass;
 * the operating empty mass;
 * the zero fuel mass;
 * the maximum amount of fuel;
 * the maximum number of passengers;
 * the maximum amount of fuel with max passengers;
 * the number of crew members needed;
 * the number of lavatories;
 * the seating disposition.

Starting point:

A)

* Main geometrical data:
* wing_area;
* wing_span;
* fuse_length;
* fuse_width.

B)

* ToolInput.xml file in the ToolInput folder.

Output:

* The code saves a user_tooloutput.xml file if case A,
  and  tooloutput.xml file if case B in the ToolOutput folder.
* The code saves a copy of the tooloutput.xml file inside the
  ToolInput folder of the range and balance analysis.
* The system creates a folder with the aircraft name, and it saves inside
  three txt file and one figure:
* NAME_Aircraft_Geometry.out: that contains all the information
  regarding the aircraft geometry (only with case B)
* NAME_Seats_disposition.out: with an example of the seat disposition.
* NAME_Weight_module.out: with all information evaluated with this code.
* NAME_mtomPrediction.png: contains the result of the linear regression
  carried on for the maximum take-off mass evaluation.
