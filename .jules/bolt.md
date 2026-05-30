## 2026-05-29 - replace_color_with_transparency Alpha channel math optimization
**Learning:** In `replace_color_with_transparency`, replacing the boolean logic of `mask_inv = ImageChops.invert(mask)` and `new_a = ImageChops.multiply(a, mask_inv)` with a single `ImageChops.subtract(a, mask)` produces mathematically identical results but requires one less image operation, improving speed.
**Action:** Replaced invert+multiply with subtract to save CPU time on high-resolution masks.
## 2026-05-29 - replace_color_with_transparency Alpha channel math optimization
**Learning:** In `replace_color_with_transparency`, replacing the boolean logic of `mask_inv = ImageChops.invert(mask)` and `new_a = ImageChops.multiply(a, mask_inv)` with a single `ImageChops.subtract(a, mask)` produces mathematically identical results but requires one less image operation, improving speed.
**Action:** Replaced invert+multiply with subtract to save CPU time on high-resolution masks.
