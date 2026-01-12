# Palette's Journal - Critical Learnings

## 2024-05-23 - Micro-UX in Streamlit
**Learning:** Streamlit abstracts away much of the HTML/CSS, so traditional accessibility fixes (like ARIA attributes on custom elements) are harder to apply directly. However, Streamlit provides parameters like `help` on most input widgets which render as tooltips. This is a powerful, built-in way to improve usability and accessibility (by explaining context) without needing custom HTML.
**Action:** Prioritize using the `help` parameter on all Streamlit widgets to provide context and instructions, especially for technical settings.

## 2024-05-24 - Onboarding via Empty States
**Learning:** In data-centric apps like this one, the "Empty State" (initial view) is often neglected, showing just a blank screen or a tiny prompt. This is a prime real estate to educate users about features they might not discover otherwise (like Vectorization or Privacy stripping).
**Action:** Always use the empty state to sell the "Why" and "What" of the application, not just the "How".
