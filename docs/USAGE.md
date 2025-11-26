# FLEXPART CLI Usage

1. Build Docker images (once):
   ```bash
   ./scripts/build_images.sh
   ```
2. Prepare CDS credentials and export file paths if desired.
3. Run CLI:
   ```bash
   python -m flexpart_app.cli run \
     /data/flexpart_runs/case01 \
     --start 2020-01-01T00:00 \
     --end 2020-01-02T00:00 \
     --latitude 45.0 --longitude 10.0 \
     --cdsapirc $HOME/.cdsapirc
   ```

The command downloads ERA5 (if `--era5/--no-era5` left default True), builds input files, runs FLEXPART, and validates outputs.
