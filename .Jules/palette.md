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

## 2024-05-26 - Preventing Cumulative Layout Shift (CLS) in Settings
**Learning:** Conditionally rendering inputs (like showing watermark opacity *only* after text is entered, or showing compression settings *only* for certain formats) causes the UI to jump around. It also leads to "post-action warnings" where a user checks a box only to be told the format doesn't support it.
**Action:** Always render dependent inputs and use the `disabled` state with a dynamic `help` tooltip to explain why they are unavailable. This prevents layout shift (CLS) and shifts the UX to Error Prevention.
