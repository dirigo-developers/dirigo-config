from datetime import datetime
from typing import Any, Optional, Union, get_args, get_origin

import customtkinter as ctk
from pydantic import BaseModel



def _is_optional(annotation: Any) -> tuple[bool, Any]:
    """
    Determine whether the field is optional based on the annotation (type hint).
    Returns (is_optional, inner_type).
    Works for `T | None` and `Optional[T]`.
    """
    origin = get_origin(annotation)
    if origin is Union:
        args = list(get_args(annotation))
        if type(None) in args:  # noqa: E721
            non_none = [a for a in args if a is not type(None)]  # noqa: E721
            inner = non_none[0] if non_none else Any
            return True, inner
    return False, annotation


def _format_datetime(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def build_form_from_model(
    parent: ctk.CTkBaseClass,
    model_cls: type[BaseModel],
    *,
    instance: BaseModel | None = None,
) -> tuple[ctk.CTkFrame, dict[str, Any], dict[str, Any]]:
    """
    Build a form for `model_cls` inside a frame.

    Returns:
      - frame: the container frame
      - getters: {field_name: callable -> python_value}
      - widgets: {field_name: widget}
    """
    frame = ctk.CTkFrame(parent, corner_radius=12)
    frame.grid_columnconfigure(1, weight=1)

    if instance is None:
        instance = model_cls()

    getters: dict[str, Any] = {}
    widgets: dict[str, Any] = {}

    row = 0
    for field_name, finfo in model_cls.model_fields.items():
        if finfo.exclude:
            continue

        ann = finfo.annotation
        is_opt, inner = _is_optional(ann)

        # Label: prefer Field(title=...) if provided; fall back to field name
        title = finfo.title or field_name.replace("_", " ").title()
        label = ctk.CTkLabel(frame, text=f"{title}:")
        label.grid(row=row, column=0, sticky="nw", padx=12, pady=(10, 4))

        desc = finfo.description or ""
        help_label = None
        if desc:
            help_label = ctk.CTkLabel(
                frame,
                text=desc,
                font=ctk.CTkFont(size=11),
                text_color=("gray30", "gray70"),
                justify="left",
                wraplength=520,
            )

        current_value = getattr(instance, field_name)

        if inner is str:
            # Choose textbox for known multiline fields or values that already contain newlines
            if field_name in ("notes",) or (isinstance(current_value, str) and "\n" in current_value):
                tb = ctk.CTkTextbox(frame, height=110, wrap="word")
                tb.grid(row=row, column=1, sticky="ew", padx=12, pady=(10, 4))
                tb.insert("1.0", current_value or "")
                widgets[field_name] = tb

                def make_getter_textbox(widget: ctk.CTkTextbox, optional: bool):
                    def _get() -> Optional[str]:
                        txt = widget.get("1.0", "end-1c").strip()
                        if optional and txt == "":
                            return None
                        return txt

                    return _get

                getters[field_name] = make_getter_textbox(tb, is_opt)
            else:
                entry = ctk.CTkEntry(frame)
                entry.grid(row=row, column=1, sticky="ew", padx=12, pady=(10, 4))
                entry.insert(0, "" if current_value is None else str(current_value))
                widgets[field_name] = entry

                def make_getter_entry(widget: ctk.CTkEntry, optional: bool):
                    def _get() -> Optional[str]:
                        txt = widget.get().strip()
                        if optional and txt == "":
                            return None
                        return txt

                    return _get

                getters[field_name] = make_getter_entry(entry, is_opt)

        elif inner is datetime:
            container = ctk.CTkFrame(frame, fg_color="transparent")
            container.grid(row=row, column=1, sticky="ew", padx=12, pady=(10, 4))
            container.grid_columnconfigure(0, weight=1)

            entry = ctk.CTkEntry(container)
            entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
            entry.insert(0, _format_datetime(current_value))
            entry.configure(state="disabled")
            widgets[field_name] = entry

            def set_now():
                entry.configure(state="normal")
                entry.delete(0, "end")
                entry.insert(0, _format_datetime(datetime.now()))
                entry.configure(state="disabled")

            btn = ctk.CTkButton(container, text="Now", width=70, command=set_now)
            btn.grid(row=0, column=1, sticky="e")

            def make_getter_datetime(widget: ctk.CTkEntry):
                def _get() -> datetime:
                    txt = widget.get().strip()
                    return datetime.strptime(txt, "%Y-%m-%d %H:%M:%S")

                return _get

            getters[field_name] = make_getter_datetime(entry)

        else:
            entry = ctk.CTkEntry(frame, placeholder_text=f"Unsupported type: {inner}")
            entry.grid(row=row, column=1, sticky="ew", padx=12, pady=(10, 4))
            entry.insert(0, "" if current_value is None else str(current_value))
            widgets[field_name] = entry
            getters[field_name] = lambda e=entry: e.get()

        if help_label:
            help_label.grid(row=row + 1, column=1, sticky="w", padx=12, pady=(0, 6))
            row += 2
        else:
            row += 1

    return frame, getters, widgets
