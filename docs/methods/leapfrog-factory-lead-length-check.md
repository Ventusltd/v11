# Leapfrog factory-lead length check

## Purpose

This method determines whether factory-fitted PV module leads are long enough to make a leapfrog inter-module connection across one intervening module.

It separates four quantities that must not be confused:

1. module width;
2. module-to-module installation gap;
3. horizontal separation between the two junction-box cable exit points on one module;
4. the length of each individual positive and negative factory lead.

The method is a geometric screening calculation. Final approval requires the manufacturer's dimensioned junction-box/lead drawing, connector mating geometry, minimum bend radius and the actual mounting/clip route.

## Source boundary

Reference module: Trina Solar TSM-DEG21C.20, 655–660 W class.

The Trina datasheet gives:

- module width: `W = 1.303 m`;
- module height: `2.384 m`;
- standard portrait factory leads: `0.350 m` and `0.280 m`;
- 4.0 mm² PV cable;
- MC4-EVO2 / TS4 connector options.

The datasheet does **not** dimension the horizontal separation between the positive and negative junction-box cable exit points and does not assign the 350 mm and 280 mm leads to polarity. That separation must therefore remain an explicit project/manufacturer input.

Reference inverter: Sungrow SG350HX, 12-MPPT configuration, two strings per MPPT and dedicated positive/negative PV connector pairs.

## Definitions

All dimensions are measured between cable exit/root points, not module frame edges or connector tips.

- `W` = module width, m.
- `g` = clear module-to-module gap, m.
- `P = W + g` = module pitch, m.
- `s` = horizontal separation between the two relevant junction-box cable roots on one module, m.
- `L_a`, `L_b` = usable lengths of the two factory leads that mate to form one inter-module connection, m.
- `L_available = L_a + L_b`.
- `k` = multiplicative routing/slack allowance, e.g. `1.10` for 10%.
- `A_fixed` = additional fixed allowance for connector approach, bends, clips and construction tolerance, m.

`usable lead length` should exclude any length trapped inside the junction box or connector body if the quoted manufacturer length is not measured from cable exit to connector datum.

## Straight-line connection geometry

Assume adjacent module centres are separated by pitch `P`, and the two relevant cable roots on each module are separated horizontally by `s`.

### Sequential connection

A sequential connection joins facing roots on adjacent modules:

```text
D_sequential = P - s
```

### Leapfrog connection

A leapfrog connection skips one physical module and joins roots on modules two pitches apart:

```text
D_leapfrog = 2P - s
```

Therefore:

```text
D_leapfrog - D_sequential = P
```

The leapfrog factory interconnect requires exactly one additional module pitch compared with the corresponding sequential interconnect. Junction-box separation cancels from the difference.

## Pass/fail test

The basic geometric test is:

```text
L_available >= D_leapfrog
```

The recommended design screening test is:

```text
L_available >= k × D_leapfrog + A_fixed
```

Equivalently, the reserve is:

```text
Reserve = L_available - (k × D_leapfrog + A_fixed)
```

A positive reserve is geometrically feasible. It is not by itself a manufacturer installation approval.

## Trina 1303 mm module worked example

Use the current V11/project assumptions:

```text
W = 1.303 m
g = 0.030 m
P = 1.333 m
s = 0.840 m  (project assumption; not dimensioned in the datasheet)
```

Then:

```text
D_sequential = 1.333 - 0.840 = 0.493 m
D_leapfrog   = 2(1.333) - 0.840 = 1.826 m
```

### Standard 350/280 mm leads

```text
L_available = 0.350 + 0.280 = 0.630 m
```

Sequential reserve before routing allowance:

```text
0.630 - 0.493 = 0.137 m
```

Leapfrog deficit before routing allowance:

```text
0.630 - 1.826 = -1.196 m
```

The standard leads are geometrically adequate for the adjacent sequential connection under these assumptions, but not for the skip-one leapfrog connection.

### 1400/1400 mm leapfrog leads

If the order means **1.4 m on each polarity lead**:

```text
L_available = 1.400 + 1.400 = 2.800 m
```

Straight-line reserve:

```text
2.800 - 1.826 = 0.974 m
```

With 10% multiplicative allowance and no fixed allowance:

```text
Required = 1.10 × 1.826 = 2.009 m
Reserve  = 2.800 - 2.009 = 0.791 m
```

With 15% allowance:

```text
Required = 1.15 × 1.826 = 2.100 m
Reserve  = 2.800 - 2.100 = 0.700 m
```

With 20% allowance:

```text
Required = 1.20 × 1.826 = 2.191 m
Reserve  = 2.800 - 2.191 = 0.609 m
```

Under the stated `s = 0.840 m` geometry, 1400/1400 mm leads are comfortably long enough.

## Why the purchase description matters

The following descriptions are not equivalent:

| Ordered lead lengths | Combined available length | Result at `D_leapfrog = 1.826 m`, before allowance |
|---|---:|---:|
| 1400 / 1400 mm | 2.800 m | PASS, 0.974 m reserve |
| 1400 / 350 mm | 1.750 m | FAIL, 0.076 m short |
| 1400 / 280 mm | 1.680 m | FAIL, 0.146 m short |
| 1400 mm total pair | 1.400 m | FAIL, 0.426 m short |

The procurement specification must state both individual usable lead lengths, for example:

```text
positive factory lead: 1400 mm usable
negative factory lead: 1400 mm usable
measurement datum: junction-box cable exit to connector mating datum
```

## Sensitivity to module gap

For `W = 1.303 m`, `s = 0.840 m` and 1400/1400 mm leads:

| Gap `g` | Pitch `P` | Leapfrog span `2P-s` | Straight reserve |
|---:|---:|---:|---:|
| 0.005 m | 1.308 m | 1.776 m | 1.024 m |
| 0.020 m | 1.323 m | 1.806 m | 0.994 m |
| 0.030 m | 1.333 m | 1.826 m | 0.974 m |
| 0.050 m | 1.353 m | 1.866 m | 0.934 m |

The conclusion is insensitive to ordinary module gaps when both leads are 1.4 m.

## Robustness when junction-box separation is unknown

The Trina datasheet does not dimension `s`. The minimum separation needed for 1400/1400 mm leads is obtained from:

```text
2.800 >= k × (2P - s) + A_fixed
```

Rearranging:

```text
s >= 2P - (2.800 - A_fixed) / k
```

For `P = 1.333 m` and no fixed allowance:

| Routing allowance `k` | Minimum `s` required |
|---:|---:|
| 1.00 | no positive minimum; even `s = 0` passes by 0.134 m |
| 1.10 | 0.121 m |
| 1.15 | 0.231 m |
| 1.20 | 0.333 m |

Thus 1400/1400 mm leads remain adequate with a 20% routing allowance provided the relevant cable roots are separated by at least 333 mm. The project assumption of 840 mm greatly exceeds that threshold, but it must be replaced by a manufacturer dimension or controlled measurement before final approval.

## Important interpretation: one lead versus two leads

A single 1.4 m lead is only 67 mm longer than the 1.333 m module pitch:

```text
1.400 - 1.333 = 0.067 m
```

That is not a sufficient standalone construction allowance for crossing one complete pitch once connector approach, bending and clipping are included.

The leapfrog connection passes because two mating 1.4 m leads provide 2.8 m combined usable length. The design must not be justified by saying simply that “one 1.4 m lead crosses the module width.”

## Required evidence before release for manufacture

Obtain and retain:

1. a dimensioned rear-view drawing showing positive and negative junction-box cable-exit coordinates;
2. confirmation of which polarity receives each ordered lead length;
3. the manufacturer's lead-length measurement datum;
4. connector plug/socket identity and mating allowance;
5. permitted minimum cable bend radius and tensile limits;
6. intended clip/support route and any required service loop;
7. a physical first-article fit test across the actual module mounting pitch;
8. confirmation that the extended-lead configuration is covered by the module certification and warranty.

## Conclusion

For a Trina 1303 mm-wide module installed at a 30 mm gap, using the project assumption of 840 mm junction-box-root separation, the skip-one leapfrog root-to-root span is approximately `1.826 m`.

- `1400/1400 mm` factory leads provide `2.800 m` combined usable length and are geometrically sufficient, with approximately `0.974 m` straight-line reserve or `0.609 m` reserve after a 20% routing allowance.
- A single 1400 mm lead, a 1400 mm total pair, or a 1400/350 mm asymmetric pair is not sufficient under the same geometry.
- Final approval remains conditional on a dimensioned Trina junction-box/lead drawing and the actual supported cable route.
