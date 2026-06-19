# Palette's Journal - Critical Learnings

## 2024-05-23 - Micro-UX in Streamlit
**Learning:** Streamlit abstracts away much of the HTML/CSS, so traditional accessibility fixes (like ARIA attributes on custom elements) are harder to apply directly. However, Streamlit provides parameters like `help` on most input widgets which render as tooltips. This is a powerful, built-in way to improve usability and accessibility (by explaining context) without needing custom HTML.
**Action:** Prioritize using the `help` parameter on all Streamlit widgets to provide context and instructions, especially for technical settings.

## 2024-05-24 - Onboarding via Empty States
**Learning:** In data-centric apps like this one, the "Empty State" (initial view) is often neglected, showing just a blank screen or a tiny prompt. This is a prime real estate to educate users about features they might not discover otherwise (like Vectorization or Privacy stripping).
**Action:** Always use the empty state to sell the "Why" and "What" of the application, not just the "How".

## 2024-05-25 - Error Prevention in Uploaders
**Learning:** While tooltips (`help`) are great for context, critical constraints (like file limits or size caps) hidden inside them often lead to user frustration when they hit an error *after* selecting files. Showing these limits explicitly via `st.caption` or labels *before* the action is taken shifts the UX from "Error Recovery" to "Error Prevention".
**Action:** Always display hard constraints (limits, formats) visibly near the input component, not just in tooltips.

## 2024-05-26 - Formatting Sliders for Clarity
**Learning:** Raw numeric sliders (like `0.0 - 2.0` or `0 - 255`) lack context and can be confusing to users. Using Streamlit's `format` parameter on `st.slider` (e.g., `format="%.1fx"` for multipliers, `format="%d%%"` for percentages) provides immediate clarity on the unit and effect of the slider. Furthermore, mapping technical values (like a 0-255 opacity) to a user-friendly 0-100 percentage scale greatly improves intuition.
**Action:** Always use explicit string formatting for sliders to indicate units (px, %, x) and map underlying technical scales to intuitive user-facing scales where appropriate.

## 2024-05-27 - Input Placeholders for Context
**Learning:** Streamlit's `st.text_input` supports a `placeholder` argument. Providing explicit examples (e.g., "e.g. © 2024 MyBrand" for a Watermark field) improves usability by guiding the user on the expected input format without adding visual clutter like extra labels.
**Action:** Always use the `placeholder` parameter for text inputs to provide clear, contextual examples.

## 2024-05-28 - Selectbox Formatting for Clarity
**Learning:** Similar to sliders, raw numerical arrays in `st.selectbox` (like `[0, 90, 180, 270]` for rotation) can lack explicit unit context for the user. Streamlit's `st.selectbox` supports a `format_func` parameter that allows the displayed label to be modified (e.g., adding a degree symbol `°`) without changing the underlying value returned to the application logic.
**Action:** Always consider using `format_func` on selectboxes to provide explicit units or more descriptive labels for technical enum values or numerical arrays.

## 2024-05-29 - Removing Visual Clutter with Collapsed Labels
**Learning:** In Streamlit, when displaying arrays of items (like a color palette) where the visual representation is self-evident or accompanied by a separate caption, repeating the label (e.g., "Color 1", "Color 2") creates unnecessary visual clutter. Using `label_visibility="collapsed"` hides the label visually while keeping it accessible for screen readers.
**Action:** Use `label_visibility="collapsed"` on repeating widgets in tight layouts when the context is clear or a custom caption is provided.

## 2024-05-30 - Transitional Empty States
**Learning:** Between an initial empty state (no data) and a completed state (processed results), there is often a "transitional state" where data exists but action is required. If the UI relies on an action button placed far from the data input or if the user flow isn't linear, users can stall in this state. Adding context-aware calls to action (CTAs) that appear specifically in this transitional phase bridges the gap.
**Action:** Always map the full user journey. Identify states where the user has provided input but the application requires further action to produce results, and add explicit instructional UI (like `st.info` with a directional icon) to guide the next step.

## 2024-06-05 - SVG Settings Contextual Disabling
**Learning:** In the vectorization (SVG) settings, options like "Color Precision" and "Gradient Threshold" were enabled even when "Black & White (Binary)" mode was selected, leading to confusion as these sliders have no effect in binary mode.
**Action:** Applied the "Error Prevention via Disabled States" pattern by dynamically setting `disabled=True` for these sliders when the color mode is "binary", and updated their `help` tooltips to clarify why they are disabled.

## 2024-06-06 - Visible Disabled States for Discoverability
**Learning:** Hiding dependent options completely (like removing Watermark settings when no text is provided) reduces discoverability and can confuse users who are looking for those settings but haven't taken the prerequisite action yet.
**Action:** Show dependent options at all times but set `disabled=True`. This acts as a "teaser" to encourage user interaction and prevents confusion about where settings are located. When disabling, update the `help` parameter to explain exactly what action is needed to enable the setting.
