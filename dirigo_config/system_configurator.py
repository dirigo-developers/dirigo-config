import re

import customtkinter as ctk
from dirigo.config.system_config import SystemMetadata, DeviceDef, SystemConfig
from dirigo.components.io import config_path

from dirigo_config.provenance import generated_by_string
from dirigo_config.ui.forms.pydantic_form import build_form_from_model
from dirigo_config.ui.forms.device_card import DeviceCard
from dirigo_config.discovery.devices import discover_kinds_and_groups



def _slugify(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"\s+", "_", s)
    s = re.sub(r"[^a-z0-9_]+", "", s)
    return s or "system"


def main() -> None:
    ctk.set_appearance_mode("Dark")  # "Light", "Dark", or "System"
    ctk.set_default_color_theme("blue")

    app = ctk.CTk()
    app.title("Dirigo System Configurator")
    app.geometry("600x800")
    app.minsize(600, 600)

    app.grid_rowconfigure(0, weight=1)
    app.grid_columnconfigure(0, weight=1)

    page = ctk.CTkScrollableFrame(
        master=app,
        corner_radius=12,
    )
    page.grid(row=0, column=0, sticky="nsew", padx=16, pady=16)
    page.grid_columnconfigure(0, weight=1)

    # Footer (row 1) pinned to bottom
    footer = ctk.CTkFrame(app, corner_radius=12)
    footer.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 16))
    footer.grid_columnconfigure(0, weight=1)

    # -------- System Metadata section --------
    meta_title = ctk.CTkLabel(
        page,
        text="System Metadata",
        font=ctk.CTkFont(size=15, weight="bold"),
    )
    meta_title.grid(row=0, column=0, sticky="w", padx=12, pady=(12, 6))

    # Create an instance with configurator provenance injected
    system_metadata = SystemMetadata()

    meta_frame, meta_getters, _ = build_form_from_model(
        parent      = page,                                     # type: ignore
        model_cls   = SystemMetadata,
        instance    = system_metadata,
    )
    meta_frame.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 12))

    # ---------- Devices section ----------
    device_cards: list[DeviceCard] = []
    kind_to_group = discover_kinds_and_groups()

    devices_title = ctk.CTkLabel(page, text="Devices", font=ctk.CTkFont(size=15, weight="bold"))
    devices_title.grid(row=2, column=0, sticky="w", padx=12, pady=(0, 8))

    device_count = 0
    next_row = 3  # first row after the Devices header

    def make_add_row(row: int) -> ctk.CTkFrame:
        """
        Create a row that contains the 'Add Device' button.
        This row is placed where the next device card will appear.
        """
        add_row = ctk.CTkFrame(page, corner_radius=12)
        add_row.grid(row=row, column=0, sticky="ew", padx=12, pady=(0, 10))
        
        # Three columns: left spacer | button | right spacer
        add_row.grid_columnconfigure(0, weight=1)
        add_row.grid_columnconfigure(1, weight=0)
        add_row.grid_columnconfigure(2, weight=1)

        def on_add_clicked() -> None:
            nonlocal device_count, next_row
            device_count += 1

            for child in add_row.winfo_children():
                child.destroy()

            # Insert the actual device card at the same row index
            card = DeviceCard(
                add_row,
                device_number = device_count,
                kind_to_group = kind_to_group,
            )
            device_cards.append(card)
            card.pack(fill="x", expand=True, padx=0, pady=0)

            # Create the next "Add Device" row just below this card
            next_row = row + 1
            make_add_row(next_row)

        add_btn = ctk.CTkButton(
            add_row,
            text    = "+ Add Device",
            width   = 160,
            command = on_add_clicked,
        )
        add_btn.grid(row=0, column=1, pady=16)

        return add_row

    # Put the first "Add Device" row where the first device card will go
    make_add_row(next_row)

    # ---------- Footer actions ----------
    footer.grid_columnconfigure(0, weight=1)  # status
    footer.grid_columnconfigure(1, weight=1)  # filename entry expands
    footer.grid_columnconfigure(2, weight=0)  # export button

    status = ctk.CTkLabel(
        footer,
        text="",
        text_color=("gray30", "gray70"),
    )
    status.grid(row=0, column=0, sticky="w", padx=12, pady=12)

    # Filename entry
    default_filename = f"{_slugify(system_metadata.name)}.system.toml"
    filename_var = ctk.StringVar(value=default_filename)

    filename_entry = ctk.CTkEntry(
        footer,
        textvariable=filename_var,
        placeholder_text="e.g. my_system.system.toml",
    )
    filename_entry.grid(row=0, column=1, sticky="ew", padx=12, pady=12)

    def on_export_clicked() -> None:
        # Get filename from footer entry
        path = config_path() / filename_var.get().strip()
        
        # ---- Build SystemMetadata from form getters (most up-to-date values)
        meta_values = {k: get() for k, get in meta_getters.items()}
        system_metadata = SystemMetadata(**meta_values)

        # ---- Build DeviceDefs from current cards
        devices: list[DeviceDef] = []
        for i, card in enumerate(device_cards, start=1):
            name = card.get_name()
            kind = card.get_kind()
            entry_point = card.get_entry_point()

            # Skip incomplete cards (or you can show an error instead)
            if not (name and kind and entry_point):
                continue

            devices.append(
                DeviceDef(
                    name=name,
                    kind=kind,
                    entry_point=entry_point,
                    config={},  # TODO later: introspected config
                )
            )

        system_config = SystemConfig(
            generated_by = generated_by_string(),  # injected provenance
            system       = system_metadata,
            devices      = devices,
        )

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(system_config.to_toml(), encoding="utf-8")
        except OSError as e:
            status.configure(text=f"Export failed: {e}")
            return

        status.configure(text=f"Exported: {path.name}")

    export_btn = ctk.CTkButton(
        footer,
        text="Export to TOML…",
        width=160,
        command=on_export_clicked,
    )
    export_btn.grid(row=0, column=2, sticky="e", padx=12, pady=12)


    app.mainloop()



if __name__ == "__main__":
    main()

