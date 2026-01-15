import customtkinter as ctk
from typing import Dict

from dirigo.config.system_config import DeviceDef

from dirigo_config.discovery.devices import discover_entry_point_names


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
            values=[EP_PLACEHOLDER],
            variable=self.entry_point_var
        )
        self.entry_point_menu.grid(row=row, column=1, sticky="ew", padx=12, pady=6)
        row += 1
        self._add_help(row, EP_DESC)
        row += 1
        self.entry_point_menu.configure(state="disabled")

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

    def get_kind(self) -> str | None:
        label = self.kind_var.get()
        if label in ("", KIND_PLACEHOLDER):
            return None
        return self._label_to_kind[label]



    # ---- future hooks ----
    # def to_device_def(self):
    #     """Return a DeviceDef instance (later)."""
    #     ...
