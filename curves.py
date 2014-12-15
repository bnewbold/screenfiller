
# Based on https://github.com/dentearl/simpleHilbertCurve
########################################
# These functions refactored from those available at 
# wikipedia for Hilbert curves http://en.wikipedia.org/wiki/Hilbert_curve
def d2xy_hilbert(n, d):
    """
    take a d value in [0, n**2 - 1] and map it to
    an x, y value (e.g. c, r).
    """
    assert(d <= n**2 - 1)
    t = d
    x = y = 0
    s = 1
    while (s < n):
        rx = 1 & (t / 2)
        ry = 1 & (t ^ rx)
        x, y = rot_hilbert(s, x, y, rx, ry)
        x += s * rx
        y += s * ry
        t /= 4
        s *= 2
    return x, y

def xy2d_hilbert(n, x, y):
    """
    take an x,y pair (what range?) and map it to a single point
    on [0, n**2 - 1]
    """
    d = 0
    s = n/2
    while (s > 0):
        rx = (x & s) > 0
        ry = (y & s) > 0
        d += s * s * ((3 * rx) ^ ry)
        x, y = rot_hilbert(s, x, y, rx, ry)
        s /= 2
    assert(d <= n**2 - 1)
    return d

def d2xy_moore(n, d):
    """
    take a d value in [0, n**2 - 1] and map it to
    an x, y value (e.g. c, r).

    n is (1 << level), and is the length of a side

    0,1     1,1

    0,0     1,0

    """
    assert(d <= n**2 - 1)
    t = d
    x = y = 0
    s = 1 # "scale"
    while (s < n/2):
        # run all but last fractal step
        rx = 1 & (t / 2)    # is t/2 even? aka, second-to-last bit of t [0, 0, 1, 1]
        ry = 1 & (t ^ rx)   # XOR of last two bits of t [0, 1, 1, 0]
        x, y = rot_hilbert(s, x, y, rx, ry)
        x += s * rx
        y += s * ry
        t /= 4
        s *= 2

    while (s < n):
        # only runs once at the end to arrange the 4x hilbert pieces
        rx = 1 & (t / 2)    # is t/2 even? aka, second-to-last bit of t [0, 0, 1, 1]
        ry = 1 ^ (1 & (t ^ rx))   # [1, 0, 0, 1]
        x, y = rot_moore(s, x, y, rx, ry)
        x += s * rx
        y += s * ry
        t /= 4
        s *= 2

    return x, y

def rot_hilbert(n, x, y, rx, ry):
    """
    rotate/flip a quadrant appropriately
    """
    if (rx, ry) == (0, 0):
        return y, x
    if (rx, ry) == (0, 1):
        return x, y
    if (rx, ry) == (1, 0):
        return (n - 1 - y), (n - 1 - x)
    if (rx, ry) == (1, 1):
        return x, y

def rot_moore(n, x, y, rx, ry):
    if (rx, ry) == (0, 0):
        return (n - 1 - y), (n - 1 - x)
    if (rx, ry) == (0, 1):
        return (n - 1 - y), (n - 1 - x)
    if (rx, ry) == (1, 0):
        return y, x
    if (rx, ry) == (1, 1):
        return y, x
