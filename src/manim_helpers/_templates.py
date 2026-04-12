import manim


def manim_text_intro(content: str, timestamp: float) -> manim.Text:
    return manim.Text(f"Intro: {content}")


def manim_text_outro(content: str, timestamp: float) -> manim.Text:
    return manim.Text(f"Outro: {content}")


def manim_bullet_points(content: str, timestamp: float) -> manim.VGroup:
    lines = content.split("\n")
    bullet_items = []
    for i, line in enumerate(lines):
        if line.strip():
            bullet = manim.Text(f"- {line.strip()}", font_size=36)
            bullet.shift(manim.UP * (2 - i * 0.8))
            bullet_items.append(bullet)
    return manim.VGroup(*bullet_items)


def manim_image_display(content: str, timestamp: float) -> manim.ImageMobject:
    # Note: In actual implementation, content would be a path to image file.
    image_placeholder = manim.Rectangle(width=8, height=6, color=manim.BLUE)
    caption = manim.Text(content, font_size=24)
    caption.next_to(image_placeholder, manim.DOWN)
    return manim.VGroup(image_placeholder, caption)


def manim_equation_display(content: str, timestamp: float) -> manim.MathTex:
    return manim.MathTex(content, font_size=48)


def manim_step_by_step(content: str, timestamp: float) -> manim.VGroup:
    steps = content.split("\n")
    step_items = []
    for i, step in enumerate(steps):
        if step.strip():
            step_text = manim.Text(f"Step {i + 1}: {step.strip()}", font_size=32)
            step_text.shift(manim.UP * (2 - i * 0.6))
            step_items.append(step_text)
    return manim.VGroup(*step_items)


def manim_graph_plot(content: str, timestamp: float) -> manim.Axes:
    axes = manim.Axes(
        x_range=[-5, 5, 1],
        y_range=[-5, 5, 1],
        x_length=8,
        y_length=6,
        axis_config={"color": manim.BLUE},
    )
    label = manim.Text(content, font_size=24)
    label.next_to(axes, manim.DOWN)
    return manim.VGroup(axes, label)


def manim_highlight_text(content: str, timestamp: float) -> manim.VGroup:
    text = manim.Text(content, font_size=40, color=manim.YELLOW)
    highlight = manim.Rectangle(
        width=text.width + 0.5,
        height=text.height + 0.3,
        color=manim.YELLOW,
        fill_opacity=0.3,
        stroke_width=2,
    )
    highlight.move_to(text.get_center())
    return manim.VGroup(highlight, text)


def manim_transformation(content: str, timestamp: float) -> manim.VGroup:
    shape = manim.Circle(radius=1, color=manim.GREEN)
    label = manim.Text(content, font_size=24)
    label.next_to(shape, manim.DOWN)
    return manim.VGroup(shape, label)


def manim_definition_box(content: str, timestamp: float) -> manim.VGroup:
    definition_text = manim.Text(content, font_size=32)
    box = manim.Rectangle(
        width=definition_text.width + 1,
        height=definition_text.height + 0.5,
        color=manim.WHITE,
        stroke_width=3,
    )
    box.move_to(definition_text.get_center())
    title = manim.Text("Definition", font_size=28, color=manim.BLUE)
    title.next_to(box, manim.UP)
    return manim.VGroup(title, box, definition_text)


def manim_proof_steps(content: str, timestamp: float) -> manim.VGroup:
    steps = content.split("\n")
    proof_items = []
    for i, step in enumerate(steps):
        if step.strip():
            step_tex = manim.MathTex(f"\\text{{Step {i + 1}: }} {step.strip()}", font_size=36)
            step_tex.shift(manim.UP * (2 - i * 0.7))
            proof_items.append(step_tex)
    return manim.VGroup(*proof_items)


def manim_comparison(content: str, timestamp: float) -> manim.VGroup:
    parts = content.split("|")
    if len(parts) >= 2:
        left_text = manim.Text(parts[0].strip(), font_size=32)
        left_text.shift(manim.LEFT * 3)
        right_text = manim.Text(parts[1].strip(), font_size=32)
        right_text.shift(manim.RIGHT * 3)
        divider = manim.Line(start=manim.UP * 2, end=manim.DOWN * 2, color=manim.WHITE)
        return manim.VGroup(left_text, divider, right_text)
    return manim.Text(content, font_size=32)


template_map = {
    "text_intro(content, timestamp)": manim_text_intro,
    "text_outro(content, timestamp)": manim_text_outro,
    "bullet_points(content, timestamp)": manim_bullet_points,
    "image_display(content, timestamp)": manim_image_display,
    "equation_display(content, timestamp)": manim_equation_display,
    "step_by_step(content, timestamp)": manim_step_by_step,
    "graph_plot(content, timestamp)": manim_graph_plot,
    "highlight_text(content, timestamp)": manim_highlight_text,
    "transformation(content, timestamp)": manim_transformation,
    "definition_box(content, timestamp)": manim_definition_box,
    "proof_steps(content, timestamp)": manim_proof_steps,
    "comparison(content, timestamp)": manim_comparison,
}
