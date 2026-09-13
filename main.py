"""
=============================================================================
  National ID Code Analyzer Pro  v1.0
  A comprehensive GUI tool for Iranian National ID code validation,
  generation, and birth-date estimation using machine learning.
=============================================================================
  Requirements:
    pip install pandas numpy scikit-learn openpyxl matplotlib
=============================================================================
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
import pickle
from datetime import datetime
from queue import Queue, Empty

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from openpyxl import Workbook

try:
    import matplotlib
    matplotlib.use("TkAgg")
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

APP_TITLE   = "National ID Code Analyzer Pro"
APP_VERSION = "1.0.0"
WIN_SIZE    = "1150x780"
PAD         = {"padx": 6, "pady": 4}
FONT_MONO   = ("Consolas", 10)
FONT_UI     = ("Segoe UI", 10)
FONT_HEAD   = ("Segoe UI", 11, "bold")
COLOR_OK    = "#27ae60"
COLOR_ERR   = "#e74c3c"
COLOR_WARN  = "#f39c12"

def is_valid_code(code: str) -> bool:
    """Validate a 10-digit Iranian National ID code (mod-11 checksum)."""
    code = str(code).strip()
    if len(code) != 10 or not code.isdigit():
        return False
    digits = [int(d) for d in code]
    s = sum(digits[i] * (10 - i) for i in range(9))
    rem = s % 11
    return digits[9] == (rem if rem < 2 else 11 - rem)


def birth8_to_ordinal(birth8) -> int | None:
    """Convert YYYYMMDD integer → ordinal day number."""
    try:
        return datetime.strptime(str(int(birth8)), "%Y%m%d").toordinal()
    except Exception:
        return None


def ordinal_to_birth8(ordinal: float) -> int | None:
    """Convert ordinal day number → YYYYMMDD integer."""
    try:
        return int(datetime.fromordinal(int(round(ordinal))).strftime("%Y%m%d"))
    except Exception:
        return None


def fmt_birth(birth8) -> str:
    """YYYYMMDD → YYYY/MM/DD."""
    s = str(int(birth8))
    return f"{s[:4]}/{s[4:6]}/{s[6:8]}" if len(s) == 8 else s


class ScrollTree(ttk.Frame):
    """Treeview with vertical + horizontal scrollbars."""
    def __init__(self, parent, columns, **kw):
        super().__init__(parent)
        self.tree = ttk.Treeview(self, columns=columns, show="headings", **kw)
        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

    def set_columns(self, cols, widths=None):
        self.tree["columns"] = cols
        for i, c in enumerate(cols):
            self.tree.heading(c, text=c)
            w = widths[i] if widths and i < len(widths) else 120
            self.tree.column(c, width=w, anchor="center")

    def clear(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

    def insert_row(self, values):
        self.tree.insert("", "end", values=values)


class ValidatorTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._build()

    def _build(self):
        frm_single = ttk.LabelFrame(self, text="Single Code Validation")
        frm_single.pack(fill="x", **PAD)

        ttk.Label(frm_single, text="Enter 10-digit code:").grid(row=0, column=0, **PAD)
        self.ent_code = ttk.Entry(frm_single, width=20, font=FONT_MONO)
        self.ent_code.grid(row=0, column=1, **PAD)
        self.ent_code.bind("<Return>", lambda e: self._validate_single())
        ttk.Button(frm_single, text="Validate", command=self._validate_single).grid(row=0, column=2, **PAD)
        self.lbl_result = ttk.Label(frm_single, text="", font=FONT_HEAD)
        self.lbl_result.grid(row=0, column=3, **PAD)

        frm_batch = ttk.LabelFrame(self, text="Batch Validation from File")
        frm_batch.pack(fill="both", expand=True, **PAD)

        row_btn = ttk.Frame(frm_batch)
        row_btn.pack(fill="x", **PAD)
        ttk.Button(row_btn, text="Load File (.txt / .csv)", command=self._load_batch).pack(side="left", **PAD)
        ttk.Button(row_btn, text="Export Results", command=self._export_batch).pack(side="left", **PAD)
        self.lbl_batch_info = ttk.Label(row_btn, text="")
        self.lbl_batch_info.pack(side="left", **PAD)

        self.tree_batch = ScrollTree(frm_batch, columns=("Code", "Status"))
        self.tree_batch.set_columns(("Code", "Status"), (200, 120))
        self.tree_batch.pack(fill="both", expand=True, **PAD)

        self.batch_results = []

    def _validate_single(self):
        code = self.ent_code.get().strip()
        if is_valid_code(code):
            self.lbl_result.config(text="✔ VALID", foreground=COLOR_OK)
        else:
            self.lbl_result.config(text="✘ INVALID", foreground=COLOR_ERR)

    def _load_batch(self):
        path = filedialog.askopenfilename(filetypes=[("Text/CSV", "*.txt *.csv"), ("All", "*.*")])
        if not path:
            return
        self.tree_batch.clear()
        self.batch_results = []
        valid = invalid = 0
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                code = line.strip().split(",")[0].strip()
                if not code or not code.isdigit():
                    continue
                ok = is_valid_code(code)
                status = "VALID" if ok else "INVALID"
                self.tree_batch.insert_row((code, status))
                self.batch_results.append((code, status))
                if ok:
                    valid += 1
                else:
                    invalid += 1
        self.lbl_batch_info.config(text=f"Total: {valid + invalid}  |  Valid: {valid}  |  Invalid: {invalid}")
        self.app.status(f"Batch validation done – {valid} valid, {invalid} invalid")

    def _export_batch(self):
        if not self.batch_results:
            messagebox.showwarning("Warning", "No results to export.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")])
        if not path:
            return
        wb = Workbook()
        ws = wb.active
        ws.title = "Validation Results"
        ws.append(["#", "Code", "Status"])
        for i, (code, status) in enumerate(self.batch_results, 1):
            ws.append([i, code, status])
        wb.save(path)
        self.app.status(f"Validation results exported → {path}")
        messagebox.showinfo("Done", f"Exported to:\n{path}")


class GeneratorTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._build()

    def _build(self):
        frm_opts = ttk.LabelFrame(self, text="Generation Parameters")
        frm_opts.pack(fill="x", **PAD)

        ttk.Label(frm_opts, text="Start:").grid(row=0, column=0, **PAD)
        self.ent_start = ttk.Entry(frm_opts, width=16, font=FONT_MONO)
        self.ent_start.grid(row=0, column=1, **PAD)
        self.ent_start.insert(0, "0010000000")

        ttk.Label(frm_opts, text="End:").grid(row=0, column=2, **PAD)
        self.ent_end = ttk.Entry(frm_opts, width=16, font=FONT_MONO)
        self.ent_end.grid(row=0, column=3, **PAD)
        self.ent_end.insert(0, "0019999999")

        ttk.Button(frm_opts, text="Generate", command=self._start_gen).grid(row=0, column=4, **PAD)
        ttk.Button(frm_opts, text="Stop", command=self._stop_gen).grid(row=0, column=5, **PAD)

        self.progress = ttk.Progressbar(self, mode="determinate")
        self.progress.pack(fill="x", **PAD)

        frm_out = ttk.LabelFrame(self, text="Output Files")
        frm_out.pack(fill="x", **PAD)
        ttk.Label(frm_out, text="TXT:").grid(row=0, column=0, **PAD)
        self.ent_txt = ttk.Entry(frm_out, width=30)
        self.ent_txt.grid(row=0, column=1, **PAD)
        self.ent_txt.insert(0, "codes.txt")
        ttk.Button(frm_out, text="Browse", command=lambda: self._browse(self.ent_txt, "save", ".txt")).grid(row=0, column=2, **PAD)

        ttk.Label(frm_out, text="Excel:").grid(row=1, column=0, **PAD)
        self.ent_xlsx = ttk.Entry(frm_out, width=30)
        self.ent_xlsx.grid(row=1, column=1, **PAD)
        self.ent_xlsx.insert(0, "codes.xlsx")
        ttk.Button(frm_out, text="Browse", command=lambda: self._browse(self.ent_xlsx, "save", ".xlsx")).grid(row=1, column=2, **PAD)

        self.txt_log = scrolledtext.ScrolledText(self, height=18, font=FONT_MONO, state="disabled")
        self.txt_log.pack(fill="both", expand=True, **PAD)

        self._stop_flag = False
        self.lbl_count = ttk.Label(self, text="")
        self.lbl_count.pack(**PAD)

    def _browse(self, entry, mode, ext):
        if mode == "save":
            p = filedialog.asksaveasfilename(defaultextension=ext, filetypes=[("File", f"*{ext}")])
        else:
            p = filedialog.askopenfilename(filetypes=[("File", f"*{ext}")])
        if p:
            entry.delete(0, "end")
            entry.insert(0, p)

    def _log(self, msg):
        self.txt_log.config(state="normal")
        self.txt_log.insert("end", msg + "\n")
        self.txt_log.see("end")
        self.txt_log.config(state="disabled")

    def _stop_gen(self):
        self._stop_flag = True

    def _start_gen(self):
        try:
            start = int(self.ent_start.get().strip())
            end = int(self.ent_end.get().strip())
        except ValueError:
            messagebox.showerror("Error", "Start and End must be integers.")
            return
        if start > end:
            messagebox.showerror("Error", "Start must be ≤ End.")
            return
        self._stop_flag = False
        self.txt_log.config(state="normal")
        self.txt_log.delete("1.0", "end")
        self.txt_log.config(state="disabled")
        self.progress["value"] = 0
        threading.Thread(target=self._gen_worker, args=(start, end), daemon=True).start()

    def _gen_worker(self, start, end):
        valid_codes = []
        total = end - start + 1
        for num in range(start, end + 1):
            if self._stop_flag:
                self.after(0, lambda: self.app.status("Generation stopped by user."))
                break
            code = str(num).zfill(10)
            if is_valid_code(code):
                valid_codes.append(code)
                self.after(0, self._log, f"#{len(valid_codes):>5}  {code}")
            pct = (num - start + 1) / total * 100
            self.after(0, self._set_progress, pct)
        else:
            txt_path = self.ent_txt.get().strip()
            xlsx_path = self.ent_xlsx.get().strip()
            if txt_path:
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(valid_codes))
            if xlsx_path:
                wb = Workbook()
                ws = wb.active
                ws.title = "Valid Codes"
                ws.append(["#", "Code"])
                for i, c in enumerate(valid_codes, 1):
                    ws.append([i, c])
                wb.save(xlsx_path)
            self.after(0, self._done, len(valid_codes), txt_path, xlsx_path)
            return
        self.after(0, self._done, len(valid_codes), "", "", stopped=True)

    def _set_progress(self, pct):
        self.progress["value"] = pct

    def _done(self, count, txt, xlsx, stopped=False):
        self.progress["value"] = 100 if not stopped else self.progress["value"]
        msg = f"{'Stopped. ' if stopped else ''}Found {count} valid codes."
        if txt or xlsx:
            msg += f"\nTXT → {txt}\nExcel → {xlsx}"
        self.lbl_count.config(text=msg)
        self.app.status(msg.split("\n")[0])
        if not stopped:
            messagebox.showinfo("Done", msg)


class TrainerTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._build()

    def _build(self):
        frm_load = ttk.LabelFrame(self, text="Training Data (CSV)")
        frm_load.pack(fill="x", **PAD)
        ttk.Button(frm_load, text="Load CSV", command=self._load_csv).pack(side="left", **PAD)
        self.lbl_csv = ttk.Label(frm_load, text="No file loaded")
        self.lbl_csv.pack(side="left", **PAD)

        self.tree_preview = ScrollTree(self, columns=("code10", "birth8", "fixed_5", "variable_5"))
        self.tree_preview.set_columns(("code10", "birth8", "fixed_5", "variable_5"), (160, 120, 100, 120))
        self.tree_preview.pack(fill="both", expand=True, **PAD)

        frm_act = ttk.Frame(self)
        frm_act.pack(fill="x", **PAD)
        ttk.Button(frm_act, text="Train Model", command=self._train).pack(side="left", **PAD)
        ttk.Button(frm_act, text="Save Model", command=self._save_model).pack(side="left", **PAD)
        ttk.Button(frm_act, text="Load Model", command=self._load_model).pack(side="left", **PAD)
        self.progress = ttk.Progressbar(frm_act, mode="indeterminate", length=200)
        self.progress.pack(side="left", **PAD)

        frm_met = ttk.LabelFrame(self, text="Model Metrics")
        frm_met.pack(fill="x", **PAD)
        self.lbl_metrics = ttk.Label(frm_met, text="Train a model to see metrics.", font=FONT_MONO)
        self.lbl_metrics.pack(**PAD)

        self.frm_chart = ttk.LabelFrame(self, text="Regression Chart")
        self.frm_chart.pack(fill="both", expand=True, **PAD)
        self.canvas_mpl = None

    def _load_csv(self):
        path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv"), ("All", "*.*")])
        if not path:
            return
        try:
            df = pd.read_csv(path)
            if "code10" not in df.columns or "birth8" not in df.columns:
                messagebox.showerror("Error", "CSV must contain 'code10' and 'birth8' columns.")
                return
            self.app.df_raw = df
            self.lbl_csv.config(text=os.path.basename(path))
            self.tree_preview.clear()
            for _, row in df.head(50).iterrows():
                self.tree_preview.insert_row((str(row["code10"]), str(row["birth8"]), "", ""))
            self.app.status(f"Loaded {len(df)} rows from CSV")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _train(self):
        if self.app.df_raw is None:
            messagebox.showwarning("Warning", "Please load a CSV file first.")
            return
        self.progress.start(10)
        threading.Thread(target=self._train_worker, daemon=True).start()

    def _train_worker(self):
        try:
            df = self.app.df_raw.copy()
            df["code10"] = df["code10"].astype(str).str.strip()
            df["birth8"] = pd.to_numeric(df["birth8"], errors="coerce")
            df["fixed_5"] = df["code10"].str[:5]
            df["variable_5"] = pd.to_numeric(df["code10"].str[5:], errors="coerce")
            df["birth_ordinal"] = df["birth8"].apply(birth8_to_ordinal)

            df_valid = df[
                df["code10"].apply(is_valid_code)
                & df["variable_5"].notna()
                & df["birth_ordinal"].notna()
            ].copy()

            if df_valid.empty:
                self.after(0, lambda: messagebox.showerror("Error", "No valid rows found in data."))
                self.after(0, self.progress.stop)
                return

            X = df_valid[["variable_5"]].values
            y = df_valid["birth_ordinal"].values

            model = LinearRegression()
            model.fit(X, y)

            y_pred = model.predict(X)
            r2 = r2_score(y, y_pred)
            mae = mean_absolute_error(y, y_pred)
            rmse = np.sqrt(mean_squared_error(y, y_pred))

            self.app.model = model
            self.app.fixed_ref = df_valid["fixed_5"].iloc[0]
            self.app.df_trained = df_valid
            self.app.metrics = {"R²": r2, "MAE": mae, "RMSE": rmse}

            self.after(0, self._show_results, r2, mae, rmse, len(df_valid), X, y, y_pred)
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Training Error", str(e)))
        finally:
            self.after(0, self.progress.stop)

    def _show_results(self, r2, mae, rmse, n, X, y, y_pred):
        txt = f"Samples: {n}  |  R²: {r2:.6f}  |  MAE: {mae:.2f} days  |  RMSE: {rmse:.2f} days"
        self.lbl_metrics.config(text=txt)
        self.app.status(f"Model trained – R²={r2:.4f}")
        messagebox.showinfo("Training Complete", txt)

        if HAS_MPL:
            for w in self.frm_chart.winfo_children():
                w.destroy()
            fig = Figure(figsize=(6, 3), dpi=100)
            ax = fig.add_subplot(111)
            ax.scatter(X, y, s=8, alpha=0.5, label="Data")
            ax.plot(X, y_pred, color="red", linewidth=2, label=f"Fit (R²={r2:.4f})")
            ax.set_xlabel("Variable Part (last 5 digits)")
            ax.set_ylabel("Birth Date (ordinal)")
            ax.legend()
            ax.set_title("Linear Regression: Code → Birth Date")
            fig.tight_layout()
            self.canvas_mpl = FigureCanvasTkAgg(fig, master=self.frm_chart)
            self.canvas_mpl.draw()
            self.canvas_mpl.get_tk_widget().pack(fill="both", expand=True)

    def _save_model(self):
        if self.app.model is None:
            messagebox.showwarning("Warning", "No model to save.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".pkl", filetypes=[("Pickle", "*.pkl")])
        if not path:
            return
        data = {
            "model": self.app.model,
            "fixed_ref": self.app.fixed_ref,
            "metrics": self.app.metrics,
        }
        with open(path, "wb") as f:
            pickle.dump(data, f)
        self.app.status(f"Model saved → {path}")
        messagebox.showinfo("Saved", f"Model saved to:\n{path}")

    def _load_model(self):
        path = filedialog.askopenfilename(filetypes=[("Pickle", "*.pkl"), ("All", "*.*")])
        if not path:
            return
        try:
            with open(path, "rb") as f:
                data = pickle.load(f)
            self.app.model = data["model"]
            self.app.fixed_ref = data["fixed_ref"]
            self.app.metrics = data.get("metrics", {})
            m = self.app.metrics
            txt = f"R²: {m.get('R²', '?'):.6f}  |  MAE: {m.get('MAE', '?'):.2f}  |  RMSE: {m.get('RMSE', '?'):.2f}"
            self.lbl_metrics.config(text=txt)
            self.app.status(f"Model loaded from {path}")
            messagebox.showinfo("Loaded", f"Model loaded.\n{txt}")
        except Exception as e:
            messagebox.showerror("Error", str(e))


class EstimatorTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._build()

    def _build(self):
        self.lbl_model_status = ttk.Label(self, text="⚠ No model loaded. Train or load a model first.", foreground=COLOR_WARN, font=FONT_HEAD)
        self.lbl_model_status.pack(fill="x", **PAD)

        frm_single = ttk.LabelFrame(self, text="Single Code Estimation")
        frm_single.pack(fill="x", **PAD)
        ttk.Label(frm_single, text="10-digit code:").grid(row=0, column=0, **PAD)
        self.ent_code = ttk.Entry(frm_single, width=20, font=FONT_MONO)
        self.ent_code.grid(row=0, column=1, **PAD)
        self.ent_code.bind("<Return>", lambda e: self._estimate_single())
        ttk.Button(frm_single, text="Estimate", command=self._estimate_single).grid(row=0, column=2, **PAD)
        self.lbl_est_result = ttk.Label(frm_single, text="", font=FONT_HEAD)
        self.lbl_est_result.grid(row=0, column=3, **PAD)

        frm_batch = ttk.LabelFrame(self, text="Batch Estimation from File")
        frm_batch.pack(fill="both", expand=True, **PAD)

        row_btn = ttk.Frame(frm_batch)
        row_btn.pack(fill="x", **PAD)
        ttk.Button(row_btn, text="Load Codes (.txt)", command=self._load_codes).pack(side="left", **PAD)
        ttk.Button(row_btn, text="Estimate All", command=self._estimate_batch).pack(side="left", **PAD)
        ttk.Button(row_btn, text="Export to Excel", command=self._export_batch).pack(side="left", **PAD)
        self.lbl_batch_info = ttk.Label(row_btn, text="")
        self.lbl_batch_info.pack(side="left", **PAD)

        self.tree_results = ScrollTree(frm_batch, columns=("Code", "Estimated Birth Date", "Formatted"))
        self.tree_results.set_columns(("Code", "Estimated Birth Date", "Formatted"), (180, 180, 160))
        self.tree_results.pack(fill="both", expand=True, **PAD)

        self.batch_results = []
        self.codes_to_estimate = []

    def _check_model(self):
        if self.app.model is None or self.app.fixed_ref is None:
            messagebox.showwarning("Warning", "Please train or load a model first (Train Model tab).")
            return False
        self.lbl_model_status.config(text=f"✔ Model active  |  Fixed prefix: {self.app.fixed_ref}", foreground=COLOR_OK)
        return True

    def _estimate_one(self, code):
        code = str(code).strip()
        if not is_valid_code(code):
            return None, "Invalid checksum"
        if code[:5] != self.app.fixed_ref:
            return None, f"Prefix mismatch (expected {self.app.fixed_ref})"
        var_part = float(code[5:])
        pred_ord = self.app.model.predict([[var_part]])[0]
        b8 = ordinal_to_birth8(pred_ord)
        if b8 is None:
            return None, "Date conversion failed"
        return b8, None

    def _estimate_single(self):
        if not self._check_model():
            return
        code = self.ent_code.get().strip()
        b8, err = self._estimate_one(code)
        if err:
            self.lbl_est_result.config(text=f"✘ {err}", foreground=COLOR_ERR)
        else:
            self.lbl_est_result.config(text=f"✔ {fmt_birth(b8)}  ({b8})", foreground=COLOR_OK)

    def _load_codes(self):
        path = filedialog.askopenfilename(filetypes=[("Text", "*.txt"), ("All", "*.*")])
        if not path:
            return
        with open(path, "r", encoding="utf-8") as f:
            self.codes_to_estimate = [l.strip() for l in f if l.strip()]
        self.lbl_batch_info.config(text=f"Loaded {len(self.codes_to_estimate)} codes")
        self.app.status(f"Loaded {len(self.codes_to_estimate)} codes for estimation")

    def _estimate_batch(self):
        if not self._check_model():
            return
        if not self.codes_to_estimate:
            messagebox.showwarning("Warning", "Load codes first.")
            return
        self.tree_results.clear()
        self.batch_results = []
        ok = 0
        for code in self.codes_to_estimate:
            b8, err = self._estimate_one(code)
            if b8:
                self.tree_results.insert_row((code, str(b8), fmt_birth(b8)))
                self.batch_results.append((code, b8))
                ok += 1
        self.lbl_batch_info.config(text=f"Estimated: {ok} / {len(self.codes_to_estimate)}")
        self.app.status(f"Batch estimation done – {ok} successful")

    def _export_batch(self):
        if not self.batch_results:
            messagebox.showwarning("Warning", "No results to export.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")])
        if not path:
            return
        df = pd.DataFrame(self.batch_results, columns=["Code", "Estimated_Birth8"])
        df["Formatted"] = df["Estimated_Birth8"].apply(fmt_birth)
        df = df.sort_values("Code", ascending=False)
        df.to_excel(path, index=False)
        self.app.status(f"Estimation results exported → {path}")
        messagebox.showinfo("Done", f"Exported to:\n{path}")


class AnalyticsTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._build()

    def _build(self):
        frm_btn = ttk.Frame(self)
        frm_btn.pack(fill="x", **PAD)
        ttk.Button(frm_btn, text="Analyze Generated/Loaded Codes", command=self._analyze).pack(side="left", **PAD)
        self.lbl_info = ttk.Label(frm_btn, text="")
        self.lbl_info.pack(side="left", **PAD)

        self.frm_chart = ttk.Frame(self)
        self.frm_chart.pack(fill="both", expand=True, **PAD)

        self.txt_stats = scrolledtext.ScrolledText(self, height=10, font=FONT_MONO, state="disabled")
        self.txt_stats.pack(fill="x", **PAD)

    def _analyze(self):
        codes = []
        if hasattr(self.app, "df_trained") and self.app.df_trained is not None:
            codes = self.app.df_trained["code10"].tolist()
        if not codes:
            messagebox.showinfo("Info", "No data available. Train a model or load codes first.")
            return

        valid = [c for c in codes if is_valid_code(str(c))]
        invalid = [c for c in codes if not is_valid_code(str(c))]
        prefixes = {}
        for c in valid:
            p = str(c)[:5]
            prefixes[p] = prefixes.get(p, 0) + 1

        stats = (
            f"Total codes analyzed : {len(codes)}\n"
            f"Valid                : {len(valid)}\n"
            f"Invalid              : {len(invalid)}\n"
            f"Unique prefixes (5)  : {len(prefixes)}\n"
        )
        for p, cnt in sorted(prefixes.items()):
            stats += f"  Prefix {p} : {cnt} codes\n"

        self.txt_stats.config(state="normal")
        self.txt_stats.delete("1.0", "end")
        self.txt_stats.insert("end", stats)
        self.txt_stats.config(state="disabled")
        self.lbl_info.config(text=f"Analyzed {len(codes)} codes")

        if HAS_MPL:
            for w in self.frm_chart.winfo_children():
                w.destroy()
            fig = Figure(figsize=(7, 3.5), dpi=100)
            ax = fig.add_subplot(111)
            if prefixes:
                ax.bar(prefixes.keys(), prefixes.values(), color="#3498db")
                ax.set_title("Code Distribution by 5-Digit Prefix")
                ax.set_xlabel("Prefix")
                ax.set_ylabel("Count")
            fig.tight_layout()
            canvas = FigureCanvasTkAgg(fig, master=self.frm_chart)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)


class MainApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"{APP_TITLE}  v{APP_VERSION}")
        self.root.geometry(WIN_SIZE)
        self.root.minsize(900, 600)

        self.model = None
        self.fixed_ref = None
        self.df_raw = None
        self.df_trained = None
        self.metrics = {}
        self.dark_mode = False

        self._build_menu()
        self._build_notebook()
        self._build_statusbar()
        self._apply_theme()

    def _build_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Exit", accelerator="Ctrl+Q", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Toggle Dark / Light Theme", command=self._toggle_theme)
        menubar.add_cascade(label="View", menu=view_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self._about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.root.bind("<Control-q>", lambda e: self.root.quit())

    def _build_notebook(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=4, pady=4)

        self.tab_validator  = ValidatorTab(self.notebook, self)
        self.tab_generator  = GeneratorTab(self.notebook, self)
        self.tab_trainer    = TrainerTab(self.notebook, self)
        self.tab_estimator  = EstimatorTab(self.notebook, self)
        self.tab_analytics  = AnalyticsTab(self.notebook, self)

        self.notebook.add(self.tab_validator,  text="  🔍  Validate  ")
        self.notebook.add(self.tab_generator,  text="  ⚙️  Generate  ")
        self.notebook.add(self.tab_trainer,    text="  🧠  Train Model  ")
        self.notebook.add(self.tab_estimator,  text="  📅  Estimate  ")
        self.notebook.add(self.tab_analytics,  text="  📊  Analytics  ")

    def _build_statusbar(self):
        self.status_var = tk.StringVar(value="Ready")
        sb = ttk.Label(self.root, textvariable=self.status_var, relief="sunken", anchor="w", padding=(8, 2))
        sb.pack(fill="x", side="bottom")

    def status(self, msg):
        self.status_var.set(msg)

    def _apply_theme(self):
        style = ttk.Style()
        available = style.theme_names()
        for t in ("clam", "alt", "default"):
            if t in available:
                style.theme_use(t)
                break

        if self.dark_mode:
            bg = "#1e1e1e"
            fg = "#d4d4d4"
            self.root.configure(bg=bg)
            style.configure(".", background=bg, foreground=fg, fieldbackground="#2d2d2d",
                            borderwidth=0, focusthickness=0)
            style.configure("TNotebook", background=bg)
            style.configure("TNotebook.Tab", background="#2d2d2d", foreground=fg, padding=[12, 4])
            style.map("TNotebook.Tab", background=[("selected", "#3c3c3c")])
            style.configure("TLabelframe", background=bg, foreground=fg)
            style.configure("TLabelframe.Label", background=bg, foreground=fg)
            style.configure("TFrame", background=bg)
            style.configure("TLabel", background=bg, foreground=fg)
            style.configure("TButton", background="#3c3c3c", foreground=fg)
            style.configure("Treeview", background="#2d2d2d", foreground=fg, fieldbackground="#2d2d2d")
            style.configure("Treeview.Heading", background="#3c3c3c", foreground=fg)
        else:
            self.root.configure(bg="#f0f0f0")
            style.configure(".", background="#f0f0f0", foreground="black", fieldbackground="white")
            style.configure("TNotebook", background="#f0f0f0")
            style.configure("TNotebook.Tab", background="#e0e0e0", foreground="black", padding=[12, 4])
            style.map("TNotebook.Tab", background=[("selected", "#ffffff")])
            style.configure("TLabelframe", background="#f0f0f0", foreground="black")
            style.configure("TLabelframe.Label", background="#f0f0f0", foreground="black")
            style.configure("TFrame", background="#f0f0f0")
            style.configure("TLabel", background="#f0f0f0", foreground="black")
            style.configure("Treeview", background="white", foreground="black", fieldbackground="white")

    def _toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self._apply_theme()
        self.status(f"Theme: {'Dark' if self.dark_mode else 'Light'}")

    def _about(self):
        messagebox.showinfo(
            "About",
            f"{APP_TITLE}\nVersion {APP_VERSION}\n\n"
            "A comprehensive tool for Iranian National ID code\n"
            "validation, generation, and birth-date estimation\n"
            "using linear regression.\n\n"
            f"Matplotlib: {'Available ✔' if HAS_MPL else 'Not installed'}"
        )

    def run(self):
        self.root.mainloop()


# ENJOY TO USE
if __name__ == "__main__":
    app = MainApp()
    app.run()
