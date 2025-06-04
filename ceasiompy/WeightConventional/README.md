<img align="right" height="70" src="../../documents/logos/CEASIOMpy_banner_weights.png">

# WeightConventional

**Categories:** Weight, Estimation

**State**: :heavy_check_mark:

`WeightConventional` module can make estimation of the following masses for conventional aircraft:

- Maximum Take-Off Mass
- Operating Empty Mass
- Zero fuel mass

It also calculates other values which are required to calculate those masses, e.g.:

- Number of abreast
- Number of passenger
- Number of cabin crew member
- Wing loading

Example of workflow with the `WeightConventional` module:

```mermaid
  graph LR;
      CPACSCreator-->WeightConventional;
      WeightConventional-->PyAVL;
```

## Inputs

`WeightConventional` takes as input a CPACS file, it use only the geometry of the aircraft to make estimations.

## Analyses

To estimate the MTOM, the `WeightConventional` module uses the following value (extracted form the CPACS geometry) from a [database](files/AircraftData2018_v3_ste.csv) of conventional aircraft, mostly based on [[2]](#CJAD).

- Wing area
- Wing Span
- Fuselage length
- Fuselage width

K-nearest neighbors regression from [scikit-learn](https://scikit-learn.org/stable/modules/generated/sklearn.neighbors.KNeighborsRegressor.html?highlight=kneighbors#sklearn.neighbors.KNeighborsRegressor.kneighbors) is used to predict the MTOM of a "new" aircraft. From this MTOM, it deduce other value from empirical relations.

From the fuselage geometry, it estimate the cabin size and a possible seat disposition to estimate the number of passenger.

## Outputs

`WeightConventional` outputs a CPACS file with the calculated masses. It also produce some markdown files in the result folder with more detail information and a figure which shows the MTOM prediction.

## Installation or requirements

`WeightConventional` is a native CEASIOMpy module, hence it is available and installed by default. To run it, you just have to be sure that you are in the CEASIOMpy Conda environment.

## Limitations

:warning: `WeightConventional` make a lot of assumption and use some empirical relationship, results may differ a lot from the reality.

:warning: `WeightConventional` is based on interpolation base on existing aircraft, it will not be able to take into account if the aircraft you design uses new technologies or materials.

## More information

## References

<a id="Picc19">[1]</a> Piccini, S.: A Weight and Balance evaluation software for conventional and unconventional aircraft design. Master Thesis (2019). [pdf](files/Master_Thesis_report_Stefano_Piccini.pdf)

<a id="CJAD">[2]</a> Jenkinson, L., Simpkin, P., Rhodes
, D.: Civil Jet Aircraft Design. Data Set. [link](https://booksite.elsevier.com/9780340741528/appendices/data-a/default.htm)
