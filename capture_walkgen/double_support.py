#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2017-2018 Stephane Caron <stephane.caron@lirmm.fr>
#
# This file is part of capture-walkgen
# <https://github.com/stephane-caron/capture-walkgen>.
#
# capture-walkgen is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# capture-walkgen is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# capture-walkgen. If not, see <http://www.gnu.org/licenses/>.

from numpy import dot, sqrt
from pymanoid.misc import normalize
from pymanoid.sim import e_z, gravity, gravity_const


class DoubleSupportController(object):

    """
    Simple controller used to stop in double support after walking. Implements
    the control law used to prove small-space controllability of the IPM in an
    Appendix of the paper.

    Parameters
    ----------
    pendulum : pymanoid.InvertedPendulum
        State estimator of the inverted pendulum.
    stance : pymanoid.Stance
        Double-support stance.
    target_height : scalar
        Desired altitude at the end of the step.
    k : scalar
        Stiffness scaling parameter.

    Notes
    -----
    The output CoM acceleration behavior will be that of a spring-damper with
    critical damping and a variable stiffness of `k * lambda(c)`. See the paper
    for details.
    """

    def __init__(self, pendulum, stance, target_height, k=1.):
        foot_center = .5 * (stance.left_foot.p + stance.right_foot.p)
        com_target = foot_center + [0., 0., target_height]
        n = normalize(stance.left_foot.n + stance.right_foot.n)
        self.com_target = com_target
        self.foot_center = foot_center
        self.k = k
        self.n = n
        self.pendulum = pendulum

    def bar(self, p):
        """
        Height coordinate for a given point.

        Parameters
        ----------
        p : array
            World coordinates.

        Returns
        -------
        h : scalar
            Height of `p`.
        """
        return dot(p, self.n) / dot(e_z, self.n)

    def compute_controls(self):
        """
        Compute controls from current state.

        Returns
        -------
        cop : array
            World coordinates of the center of pressure.
        lambda_ : scalar
            Stiffness for the inverted pendulum.
        """
        k = self.k
        com = self.pendulum.com.p
        comd = self.pendulum.com.pd
        delta_com = com - self.com_target
        v = self.bar(comd) * k
        delta_z = 4 * self.bar(com - self.foot_center) \
            + 4 * k ** 2 * self.bar(delta_com)
        omega = 2 * (sqrt(gravity_const * delta_z + v ** 2) - v) / delta_z
        lambda_ = omega ** 2
        cop = com + delta_com * k ** 2 + k * comd / omega + gravity / lambda_
        return cop, lambda_
