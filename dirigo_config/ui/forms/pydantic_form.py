from typing import Any, Optional, Union, get_args, get_origin
import types

import customtkinter as ctk
from pydantic import BaseModel
from pydantic_core import PydanticUndefined

from dirigo.components.units import RangeWithUnits



def _is_optional(annotation: Any) -> tuple[bool, Any]:
    """
    Returns (is_optional, inner_type) for:
      - Optional[T]
      - Union[T, None]
      - T | None   (PEP 604)
    """
    origin = get_origin(annotation)

    if origin in (Union, types.UnionType):
        args = get_args(annotation)
        if type(None) in args:  # noqa: E721
            non_none = [a for a in args if a is not type(None)]  # noqa: E721
            # If it's Optional[T], there should be exactly one non-None.
            inner = non_none[0] if len(non_none) == 1 else Union[tuple(non_none)]  # type: ignore[misc]
            return True, inner

    return False, annotation


def _field_default_to_str(finfo: Any) -> str:
    """
    Return a reasonable string initial value for a field based on its default.
    If no default is provided, return "".
    """
    default = finfo.default
    if default is PydanticUndefined:
        return ""
    if default is None:
        return ""
    return str(default)


def _ui_hidden(finfo) -> bool:
    extra = finfo.json_schema_extra or {}
    ui = extra.get("ui") or {}
    return bool(ui.get("hidden", False))


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

    getters: dict[str, Any] = {}
    widgets: dict[str, Any] = {}

    row = 0
    for field_name, finfo in model_cls.model_fields.items():
        if finfo.exclude:
            continue
        if _ui_hidden(finfo):
            continue

        ann = finfo.annotation
        is_opt, inner = _is_optional(ann)

        # Label: prefer Field(title=...) if provided; fall back to field name
        title = finfo.title or field_name.replace("_", " ").title()
        
        # If no instance is provided, show required fields with a "*"
        required = (not is_opt) and (finfo.default is PydanticUndefined)

        label_text = f"{title}:"
        if required:
            label_text = f"{title}: *"

        label = ctk.CTkLabel(frame, text=label_text)
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

        if instance is not None:
            current_value = getattr(instance, field_name)
        else:
            current_value = _field_default_to_str(finfo)

        if issubclass(inner, RangeWithUnits):
            container = ctk.CTkFrame(frame, fg_color="transparent")
            container.grid(row=row, column=1, sticky="ew", padx=12, pady=(10, 4))

            # Layout:  Min: [entry]   Max: [entry]
            container.grid_columnconfigure(0, weight=0)  # "Min:"
            container.grid_columnconfigure(1, weight=1)  # min entry
            container.grid_columnconfigure(2, weight=0)  # "Max:"
            container.grid_columnconfigure(3, weight=1)  # max entry

            min_label = ctk.CTkLabel(container, text="Min:")
            min_label.grid(row=0, column=0, sticky="w", padx=(0, 6))

            min_entry = ctk.CTkEntry(container)
            min_entry.grid(row=0, column=1, sticky="ew", padx=(0, 12))

            max_label = ctk.CTkLabel(container, text="Max:")
            max_label.grid(row=0, column=2, sticky="w", padx=(0, 6))

            max_entry = ctk.CTkEntry(container)
            max_entry.grid(row=0, column=3, sticky="ew")

            # Seed values from instance / defaults
            # mn0, mx0 = _range_seed_values(current_value, finfo)
            # if mn0:
            #     min_entry.insert(0, mn0)
            # if mx0:
            #     max_entry.insert(0, mx0)

            widgets[field_name] = (min_entry, max_entry)

            def make_getter_range(
                mn_w: ctk.CTkEntry,
                mx_w: ctk.CTkEntry,
                optional: bool,
            ):
                def _get():
                    mn = mn_w.get().strip()
                    mx = mx_w.get().strip()

                    if mn == "" and mx == "":
                        return None if optional else {"min": "", "max": ""}

                    # Let pydantic enforce completeness / validity
                    return {"min": mn, "max": mx}

                return _get

            getters[field_name] = make_getter_range(min_entry, max_entry, is_opt)

        elif inner is str:
            # Choose textbox for known multiline fields or values that already contain newlines
            if field_name in ("notes",) or (isinstance(current_value, str) and "\n" in current_value):
                tb = ctk.CTkTextbox(frame, height=65, wrap="word")
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

        else:
            # For now, just show an entry that accepts a string; device config validation
            # will happen when you construct the config model on export.
            entry = ctk.CTkEntry(frame, placeholder_text=f"Unsupported type: {inner}")
            entry.grid(row=row, column=1, sticky="ew", padx=12, pady=(10, 4))
            entry.insert(0, "" if current_value is None else str(current_value))
            widgets[field_name] = entry
            
            # Return raw string; config model parsing/validators should handle conversion.
            getters[field_name] = lambda e=entry, optional=is_opt: (None if (optional and e.get().strip() == "") else e.get().strip())

        if help_label:
            help_label.grid(row=row + 1, column=1, sticky="w", padx=12, pady=(0, 6))
            row += 2
        else:
            row += 1

    return frame, getters, widgets
