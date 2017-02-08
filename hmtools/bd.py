#
#   Copyright 2017 Gabriel Cebrian
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import math
import numpy
import scipy.integrate
import scipy.interpolate

def bdrate(base, test):
    """Calculates the BD-rate using the piecewise cubic interpolation function.

    Keyword arguments:
    base -- Array of tuples of the baseline points in the form (bitrate psnr),
            in increasing bitrate order.
    test -- Array of tuples of the test points in the form (bitrate psnr), in
            increasing bitrate order.
    """
    base_rate = [point[0] for point in base]
    base_psnr = [point[1] for point in base]
    test_rate = [point[0] for point in test]
    test_psnr = [point[1] for point in test]

    base_log_rate = numpy.log(base_rate)
    test_log_rate = numpy.log(test_rate)

    min_psnr = max(min(base_psnr), min(test_psnr))
    max_psnr = min(max(base_psnr), max(test_psnr))

    base_polynomial = scipy.interpolate.PchipInterpolator(base_psnr,
            base_log_rate)
    test_polynomial = scipy.interpolate.PchipInterpolator(test_psnr,
            test_log_rate)

    base_integral_value = scipy.integrate.quad(base_polynomial, min_psnr,
            max_psnr)[0];
    test_integral_value = scipy.integrate.quad(test_polynomial, min_psnr,
            max_psnr)[0];

    average = (test_integral_value - base_integral_value) \
              / (max_psnr - min_psnr)

    return (math.exp(average) - 1) * 100;

def bdrate_old(base, test):
    """Calculates the BD-rate using the cubic polynomial interpolation function.

    Keyword arguments:
    base -- Array of tuples of the baseline points in the form (bitrate psnr).
    test -- Array of tuples of the test points in the form (bitrate psnr).
    """
    base_rate = [point[0] for point in base]
    base_psnr = [point[1] for point in base]
    test_rate = [point[0] for point in test]
    test_psnr = [point[1] for point in test]

    base_log_rate = numpy.log(base_rate)
    test_log_rate = numpy.log(test_rate)

    min_psnr = max(min(base_psnr), min(test_psnr))
    max_psnr = min(max(base_psnr), max(test_psnr))

    base_polynomial = numpy.polyfit(base_psnr, base_log_rate, 3)
    test_polynomial = numpy.polyfit(test_psnr, test_log_rate, 3)

    base_integral = numpy.polyint(base_polynomial);
    test_integral = numpy.polyint(test_polynomial);

    base_integral_value = numpy.polyval(base_integral, max_psnr) \
                          - numpy.polyval(base_integral, min_psnr)
    test_integral_value = numpy.polyval(test_integral, max_psnr) \
                          - numpy.polyval(test_integral, min_psnr)

    average = (test_integral_value - base_integral_value) \
              / (max_psnr - min_psnr)

    return (math.exp(average) - 1) * 100;
