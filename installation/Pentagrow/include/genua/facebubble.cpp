
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
 
#include "facebubble.h"

FaceBubble::FaceBubble(const Face & f)
{
  // construction, produce edges with correct directions  
  const Triangulation *srf = f.surface();
  assert(srf != 0);
  pt1 = srf->vertex(f.vertex(1));
  pt2 = srf->vertex(f.vertex(2));
  pt3 = srf->vertex(f.vertex(3));
  vn1 = srf->normal(f.vertex(1));
  vn2 = srf->normal(f.vertex(2));
  vn3 = srf->normal(f.vertex(3));
}

Vct3 FaceBubble::eval(Real xi,Real eta) const
{
  // evaluate bicubic surface over face which interpolates
  // vertex normals

  Vct3 cap;

  // intercept corner values
  if (xi == 0 and eta == 0)
    return pt1;
  else if (xi == 1 and eta == 0)
    return pt2;
  else if (xi == 0 and eta == 1)
    return pt3;

  Real t10;
  Real t103;
  Real t104;
  Real t106;
  Real t107;
  Real t108;
  Real t11;
  Real t111;
  Real t113;
  Real t115;
  Real t116;
  Real t117;
  Real t12;
  Real t120;
  Real t121;
  Real t125;
  Real t126;
  Real t128;
  Real t13;
  Real t132;
  Real t133;
  Real t134;
  Real t14;
  Real t140;
  Real t141;
  Real t142;
  Real t143;
  Real t144;
  Real t145;
  Real t146;
  Real t147;
  Real t148;
  Real t149;
  Real t15;
  Real t150;
  Real t151;
  Real t153;
  Real t155;
  Real t158;
  Real t16;
  Real t161;
  Real t162;
  Real t163;
  Real t164;
  Real t165;
  Real t166;
  Real t168;
  Real t17;
  Real t171;
  Real t172;
  Real t173;
  Real t174;
  Real t175;
  Real t178;
  Real t18;
  Real t181;
  Real t185;
  Real t188;
  Real t189;
  Real t19;
  Real t190;
  Real t192;
  Real t194;
  Real t197;
  Real t198;
  Real t20;
  Real t201;
  Real t202;
  Real t207;
  Real t208;
  Real t21;
  Real t210;
  Real t211;
  Real t214;
  Real t216;
  Real t218;
  Real t219;
  Real t22;
  Real t220;
  Real t223;
  Real t224;
  Real t228;
  Real t23;
  Real t230;
  Real t234;
  Real t235;
  Real t24;
  Real t241;
  Real t242;
  Real t243;
  Real t245;
  Real t247;
  Real t25;
  Real t250;
  Real t253;
  Real t254;
  Real t255;
  Real t256;
  Real t257;
  Real t258;
  Real t26;
  Real t260;
  Real t263;
  Real t264;
  Real t265;
  Real t266;
  Real t27;
  Real t271;
  Real t274;
  Real t275;
  Real t276;
  Real t278;
  Real t28;
  Real t280;
  Real t283;
  Real t284;
  Real t287;
  Real t288;
  Real t29;
  Real t293;
  Real t294;
  Real t296;
  Real t3;
  Real t30;
  Real t301;
  Real t302;
  Real t305;
  Real t306;
  Real t31;
  Real t311;
  Real t315;
  Real t32;
  Real t323;
  Real t324;
  Real t325;
  Real t329;
  Real t33;
  Real t330;
  Real t335;
  Real t336;
  Real t337;
  Real t34;
  Real t341;
  Real t342;
  Real t35;
  Real t350;
  Real t351;
  Real t352;
  Real t356;
  Real t36;
  Real t361;
  Real t362;
  Real t363;
  Real t367;
  Real t37;
  Real t375;
  Real t376;
  Real t377;
  Real t38;
  Real t385;
  Real t386;
  Real t387;
  Real t39;
  Real t396;
  Real t397;
  Real t4;
  Real t40;
  Real t401;
  Real t402;
  Real t405;
  Real t406;
  Real t41;
  Real t410;
  Real t411;
  Real t417;
  Real t418;
  Real t422;
  Real t425;
  Real t426;
  Real t43;
  Real t430;
  Real t436;
  Real t437;
  Real t44;
  Real t443;
  Real t444;
  Real t45;
  Real t46;
  Real t48;
  Real t49;
  Real t5;
  Real t50;
  Real t51;
  Real t54;
  Real t56;
  Real t57;
  Real t58;
  Real t59;
  Real t6;
  Real t60;
  Real t61;
  Real t63;
  Real t66;
  Real t68;
  Real t69;
  Real t7;
  Real t70;
  Real t71;
  Real t78;
  Real t8;
  Real t81;
  Real t82;
  Real t83;
  Real t85;
  Real t87;
  Real t88;
  Real t9;
  Real t90;
  Real t92;
  Real t93;
  Real t94;
  Real t97;
  Real t98;
  {
    t3 = xi+eta;
    t4 = pt2[0];
    t5 = pt1[0];
    t6 = -t4+t5;
    t7 = fabs(t6);
    t8 = t7*t7;
    t9 = pt2[1];
    t10 = pt1[1];
    t11 = t9-t10;
    t12 = fabs(t11);
    t13 = t12*t12;
    t14 = pt2[2];
    t15 = pt1[2];
    t16 = t14-t15;
    t17 = fabs(t16);
    t18 = t17*t17;
    t19 = t8+t13+t18;
    t20 = sqrt(t19);
    t21 = pt3[0];
    t22 = t21-t4;
    t23 = fabs(t22);
    t24 = t23*t23;
    t25 = pt3[1];
    t26 = t25-t9;
    t27 = fabs(t26);
    t28 = t27*t27;
    t29 = pt3[2];
    t30 = t29-t14;
    t31 = fabs(t30);
    t32 = t31*t31;
    t33 = t24+t28+t32;
    t34 = sqrt(t33);
    t35 = 1/t34;
    t36 = t20*t35;
    t37 = -t6;
    t38 = xi*t37;
    t39 = t21-t5;
    t40 = eta*t39;
    t41 = t38+t40;
    t43 = xi*t11;
    t44 = t25-t10;
    t45 = eta*t44;
    t46 = t43+t45;
    t48 = xi*t16;
    t49 = t29-t15;
    t50 = eta*t49;
    t51 = t48+t50;
    t54 = fabs(t41*t37+t46*t11+t51*t16);
    t56 = fabs(-t41);
    t57 = t56*t56;
    t58 = fabs(t46);
    t59 = t58*t58;
    t60 = fabs(t51);
    t61 = t60*t60;
    t63 = sqrt(t57+t59+t61);
    t66 = 1/t20;
    t68 = (0.1E1<t54/t63*t66 ? 0.1E1 : t54/t63*t66);
    t69 = t68*t68;
    t70 = 1.0-t69;
    t71 = sqrt(t70);
    t78 = fabs(-t22*t6+t26*t11+t30*t16);
    t81 = (t78*t35*t66<0.1E1 ? t78*t35*t66 : 0.1E1);
    t82 = acos(t81);
    t83 = acos(t68);
    t85 = sin(t82+t83);
    t87 = t71/t85;
    t88 = vn2[1];
    t90 = vn2[0];
    t92 = t22*t88-t26*t90;
    t93 = t88*t92;
    t94 = vn2[2];
    t97 = t30*t90-t22*t94;
    t98 = t94*t97;
    t103 = t19/t33;
    t104 = t85*t85;
    t106 = t70/t104;
    t107 = 3.0*t4;
    t108 = 3.0*t21;
    t111 = vn3[1];
    t113 = vn3[0];
    t115 = t22*t111-t26*t113;
    t116 = t111*t115;
    t117 = vn3[2];
    t120 = t30*t113-t22*t117;
    t121 = t117*t120;
    t125 = t20*t19;
    t126 = t34*t33;
    t128 = t125/t126;
    t132 = t71*t70/t104/t85;
    t133 = 2.0*t4;
    t134 = 2.0*t21;
    t140 = 1.0-xi;
    t141 = fabs(t39);
    t142 = t141*t141;
    t143 = fabs(t44);
    t144 = t143*t143;
    t145 = fabs(t49);
    t146 = t145*t145;
    t147 = t142+t144+t146;
    t148 = sqrt(t147);
    t149 = 1/t148;
    t150 = t34*t149;
    t151 = t5+t38+t40-t4;
    t153 = t10+t43+t45-t9;
    t155 = t15+t48+t50-t14;
    t158 = fabs(t22*t151+t26*t153+t30*t155);
    t161 = fabs(-t151);
    t162 = t161*t161;
    t163 = fabs(t153);
    t164 = t163*t163;
    t165 = fabs(t155);
    t166 = t165*t165;
    t168 = sqrt(t162+t164+t166);
    t171 = (0.1E1<t158*t35/t168 ? 0.1E1 : t158*t35/t168);
    t172 = t171*t171;
    t173 = 1.0-t172;
    t174 = sqrt(t173);
    t175 = -t39;
    t178 = -t44;
    t181 = -t49;
    t185 = fabs(-t175*t22-t178*t26-t181*t30);
    t188 = (0.1E1<t185*t149*t35 ? 0.1E1 : t185*t149*t35);
    t189 = acos(t188);
    t190 = acos(t171);
    t192 = sin(t189+t190);
    t194 = t174/t192;
    t197 = t175*t111-t178*t113;
    t198 = t111*t197;
    t201 = t181*t113-t175*t117;
    t202 = t117*t201;
    t207 = t33/t147;
    t208 = t192*t192;
    t210 = t173/t208;
    t211 = 3.0*t5;
    t214 = vn1[1];
    t216 = vn1[0];
    t218 = t175*t214-t178*t216;
    t219 = t214*t218;
    t220 = vn1[2];
    t223 = t181*t216-t175*t220;
    t224 = t220*t223;
    t228 = t148*t147;
    t230 = t126/t228;
    t234 = t174*t173/t208/t192;
    t235 = 2.0*t5;
    t241 = 1.0-eta;
    t242 = t148*t66;
    t243 = t5+t38+t40-t21;
    t245 = t10+t43+t45-t25;
    t247 = t15+t48+t50-t29;
    t250 = fabs(-t175*t243-t178*t245-t181*t247);
    t253 = fabs(-t243);
    t254 = t253*t253;
    t255 = fabs(t245);
    t256 = t255*t255;
    t257 = fabs(t247);
    t258 = t257*t257;
    t260 = sqrt(t254+t256+t258);
    t263 = (t250*t149/t260<0.1E1 ? t250*t149/t260 : 0.1E1);
    t264 = t263*t263;
    t265 = 1.0-t264;
    t266 = sqrt(t265);
    t271 = fabs(t39*t37+t44*t11+t49*t16);
    t274 = (0.1E1<t271*t149*t66 ? 0.1E1 : t271*t149*t66);
    t275 = acos(t274);
    t276 = acos(t263);
    t278 = sin(t275+t276);
    t280 = t266/t278;
    t283 = t37*t214-t11*t216;
    t284 = t214*t283;
    t287 = t16*t216-t37*t220;
    t288 = t220*t287;
    t293 = t147/t19;
    t294 = t278*t278;
    t296 = t265/t294;
    t301 = t37*t88-t11*t90;
    t302 = t88*t301;
    t305 = t16*t90-t37*t94;
    t306 = t94*t305;
    t311 = t228/t125;
    t315 = t266*t265/t294/t278;
    cap[0] =
 t3*(t36*t87*(t93-t98-t21+t4)+t103*t106*(-t107+t108-2.0*t93+2.0*t98
-t116+t121)+t128*t132*(t133-t134+t93-t98+t116-t121))+t140*(t150*t194*(
t198-t202
-t5+t21)+t207*t210*(-t108+t211-2.0*t198+2.0*t202-t219+t224)+t230*t234*
(t134-
t235+t198-t202+t219-t224))+t241*(t242*t280*(t284-t288-t4+t5)+t293*t296
*(-t211+
t107-2.0*t284+2.0*t288-t302+t306)+t311*t315*(t235-t133+t284-t288+t302-
t306))+t5
+t38+t40;
    t323 = t26*t94-t30*t88;
    t324 = t94*t323;
    t325 = t90*t92;
    t329 = 3.0*t9;
    t330 = 3.0*t25;
    t335 = t26*t117-t30*t111;
    t336 = t117*t335;
    t337 = t113*t115;
    t341 = 2.0*t9;
    t342 = 2.0*t25;
    t350 = t178*t117-t181*t111;
    t351 = t117*t350;
    t352 = t113*t197;
    t356 = 3.0*t10;
    t361 = t178*t220-t181*t214;
    t362 = t220*t361;
    t363 = t216*t218;
    t367 = 2.0*t10;
    t375 = t11*t220-t16*t214;
    t376 = t220*t375;
    t377 = t216*t283;
    t385 = t11*t94-t16*t88;
    t386 = t94*t385;
    t387 = t90*t301;
    cap[1] = t3*(t36*t87*(t324-t325-t25+t9)+t103*t106*(-t329+t330-2.0*t324+2.0*
t325-t336+t337)+t128*t132*(t341-t342+t324-t325+t336-t337))+t140*(t150*
t194*(t351-t352-t10+t25)+t207*t210*(-t330+t356-2.0*t351+2.0*t352-t362+t363)+
t230*t234*(t342-t367+t351-t352+t362-t363))+t241*(t242*t280*(t376-t377-t9+t10)+t293*t296*
(-t356+t329-2.0*t376+2.0*t377-t386+t387)+t311*t315*(t367-t341+t376-t377+t386-t387))+t10+t43+t45;
    t396 = t90*t97;
    t397 = t88*t323;
    t401 = 3.0*t14;
    t402 = 3.0*t29;
    t405 = t113*t120;
    t406 = t111*t335;
    t410 = 2.0*t14;
    t411 = 2.0*t29;
    t417 = t113*t201;
    t418 = t111*t350;
    t422 = 3.0*t15;
    t425 = t216*t223;
    t426 = t214*t361;
    t430 = 2.0*t15;
    t436 = t216*t287;
    t437 = t214*t375;
    t443 = t90*t305;
    t444 = t88*t385;
    cap[2] =
 t3*(t36*t87*(t396-t397-t29+t14)+t103*t106*(-t401+t402-2.0*t396+2.0*t397-t405+t406)+
t128*t132*(t410-t411+t396-t397+t405-t406))+t140*(t150*t194*(
t417-t418-t15+t29)+t207*t210*(-t402+t422-2.0*t417+2.0*t418-t425+t426)+t230*t234*
(t411-t430+t417-t418+t425-t426))+t241*(t242*t280*(t436-t437-t14+t15)+t293*t296*
(-t422+t401-2.0*t436+2.0*t437-t443+t444)+t311*t315*(t430-t410+t436-t437+t443-t444))
+t15+t48+t50;
     }

  return cap;
}

