import customtkinter as ctk
from typing import Dict

from dirigo.config.system_config import DeviceDef

from dirigo_config.discovery.devices import (
    discover_entry_point_names, load_device_class,
    EntryPointNotFound, EntryPointNotUnique, EntryPointInvalidType
)
from dirigo_config.ui.forms.pydantic_form import build_form_from_model



NAME_DESC = DeviceDef.model_fields["name"].description or ""
KIND_DESC = DeviceDef.model_fields["kind"].description or ""
EP_DESC = DeviceDef.model_fields["entry_point"].description or ""

KIND_PLACEHOLDER = "Select device kind…"
EP_PLACEHOLDER = "Select entry point name…"



def _kind_to_label(kind: str) -> str:
    # "line_camera" -> "Line camera"
    return kind.replace("_", " ").capitalize()


def _label_to_kind(label: str) -> str:
    # "Line camera" -> "line_camera"
    return label.lower().replace(" ", "_")


class DeviceCard(ctk.CTkFrame):
    def __init__(
        self,
        parent: ctk.CTkBaseClass,
        *,
        device_number: int,
        kind_to_group: Dict[str, str],
    ) -> None:
        super().__init__(parent, corner_radius=12)

        self.kind_to_group = kind_to_group
        self.device_number = device_number

        self.grid_columnconfigure(1, weight=1)

        self._build_ui()

    def _build_ui(self) -> None:
        row = 0
        title = ctk.CTkLabel(
            self,
            text=f"Device {self.device_number}",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        title.grid(row=0, column=0, columnspan=2, sticky="w", padx=12, pady=(10, 6))
        row += 1
        
        # ---------- Device Name ----------
        ctk.CTkLabel(self, text="Device Name:").grid(row=row, column=0, sticky="w", padx=12, pady=(6, 6))
        self.name_entry = ctk.CTkEntry(self, placeholder_text="e.g. 'main digitizer', 'fast axis scanner'")
        self.name_entry.grid(row=row, column=1, sticky="ew", padx=12, pady=(6, 6))
        row += 1
        self._add_help(row, NAME_DESC)
        row += 1

        # ---------- Kind ----------
        ctk.CTkLabel(self, text="Kind:").grid(
            row=row, column=0, sticky="w", padx=12, pady=6
        )

        kinds = sorted(self.kind_to_group.keys())
        kind_labels = [_kind_to_label(k) for k in kinds]

        self._label_to_kind = dict(zip(kind_labels, kinds))
        self._kind_to_label = dict(zip(kinds, kind_labels))

        self.kind_var = ctk.StringVar(value=KIND_PLACEHOLDER)
        self.kind_menu = ctk.CTkOptionMenu(
            self,
            values   = [KIND_PLACEHOLDER] + kind_labels,
            variable = self.kind_var,
            command  = self._on_kind_change,
        )
        self.kind_menu.grid(row=row, column=1, sticky="ew", padx=12, pady=6)
        row += 1
        self._add_help(row, KIND_DESC)
        row += 1

        # Entry point dropdown
        ctk.CTkLabel(self, text="Entry point:").grid(
            row=row, column=0, sticky="w", padx=12, pady=6
        )

        self.entry_point_var = ctk.StringVar(value=EP_PLACEHOLDER)
        self.entry_point_menu = ctk.CTkOptionMenu(
            self, 
            values   = [EP_PLACEHOLDER],
            variable = self.entry_point_var,
            command  = self._on_name_change
        )
        self.entry_point_menu.grid(row=row, column=1, sticky="ew", padx=12, pady=6)
        row += 1
        self._add_help(row, EP_DESC)
        row += 1
        self.entry_point_menu.configure(state="disabled")

        # ---------- Config (auto-generated) ----------
        self.config_container = ctk.CTkFrame(self, corner_radius=12)
        self.config_container.grid(row=row, column=0, columnspan=2, sticky="ew", padx=12, pady=(6, 12))
        self.config_container.grid_columnconfigure(0, weight=1)

        self._config_model_cls = None
        self._config_getters = {}

        self._set_config_placeholder("Select an entry point to configure this device.")
        row += 1

    def _add_help(self, row: int, text: str) -> None:
        if not text:
            return
        help_label = ctk.CTkLabel(
            self,
            text=text,
            font=ctk.CTkFont(size=11),
            text_color=("gray30", "gray70"),
            justify="left",
            wraplength=520,
        )
        help_label.grid(row=row, column=1, sticky="w", padx=12, pady=(0, 6))

    def _set_config_placeholder(self, text: str) -> None:
        for child in self.config_container.winfo_children():
            child.destroy()
        lbl = ctk.CTkLabel(self.config_container, text=text, text_color=("gray30", "gray70"))
        lbl.grid(row=0, column=0, sticky="w", padx=12, pady=12)
        self._config_model_cls = None
        self._config_getters = {}

    def _clear_config_area(self) -> None:
        for child in self.config_container.winfo_children():
            child.destroy()

    def _on_kind_change(self, selected_label: str) -> None:
        if selected_label == KIND_PLACEHOLDER:
            self.entry_point_menu.configure(
                values=[EP_PLACEHOLDER],
                state="disabled",
            )
            self.entry_point_var.set(EP_PLACEHOLDER)
            return

        kind = self._label_to_kind[selected_label]
        group = self.kind_to_group.get(kind, "")
        eps = discover_entry_point_names(group) if group else []

        if eps:
            self.entry_point_menu.configure(
                values=[EP_PLACEHOLDER] + eps,
                state="normal",
            )
            self.entry_point_var.set(EP_PLACEHOLDER)
        else:
            self.entry_point_menu.configure(
                values=["(no entry points found)"],
                state="disabled",
            )
            self.entry_point_var.set("(no entry points found)")

    def _on_name_change(self, selected_label: str) -> None:
        self._clear_config_area()

        kind = self.get_kind()
        if kind is None:
            self._set_config_placeholder("Select a kind first.")
            return
        
        group = self.kind_to_group.get(kind, "")
        if not group:
            self._set_config_placeholder("Internal error: could not resolve entry point group.")
            return

        if selected_label in ("", EP_PLACEHOLDER, "(no entry points found)"):
            self._set_config_placeholder("Select an entry point to configure this device.")
            return

        try:
            device_cls = load_device_class(group, selected_label)
        except (EntryPointNotFound, EntryPointNotUnique, EntryPointInvalidType) as e:
            self._set_config_placeholder(str(e))
            return

        model_cls = getattr(device_cls, "config_model", None)
        if model_cls is None:
            self._set_config_placeholder("This device has no configurable fields.")
            return
        
        # Build the auto form
        form_frame, getters, _ = build_form_from_model(
            parent    = self.config_container,  # type: ignore
            model_cls = model_cls,
            instance  = None,
        )
        form_frame.grid(row=1, column=0, sticky="ew", padx=0, pady=0)

        self._config_model_cls = model_cls
        self._config_getters = getters

    def get_name(self) -> str | None:
        txt = (self.name_entry.get() or "").strip()
        return txt or None

    def get_kind(self) -> str | None:
        label = self.kind_var.get()
        if label in ("", KIND_PLACEHOLDER):
            return None
        return self._label_to_kind[label]
    
    def get_entry_point(self) -> str | None:
        ep = self.entry_point_var.get()
        if ep in ("", EP_PLACEHOLDER, "(none)", "(no entry points found)"):
            return None
        return ep


