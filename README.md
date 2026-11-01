# ParkirIn

Estimasi **jumlah slot kosong parkiran motor** per blok dari foto, memakai YOLOv8, dengan dashboard Streamlit untuk menampilkan hasilnya.

Foto diambil per blok (ROW1-ROW8, blok A-F) pada dua waktu, pagi dan malam. Model menghitung motor **barisan depan** di tiap foto, lalu `slot kosong = kapasitas blok - motor terdeteksi`.

## Fitur

- Deteksi motor barisan depan dengan YOLOv8m yang di-fine-tune (satu kelas: `motor_depan`).
- Slot kosong per blok, total per ROW, dan okupansi per sesi (pagi / malam).
- Status per blok dengan kode warna: **merah** (penuh), **kuning** (sebagian kosong), **hijau** (banyak kosong).
- Dashboard Streamlit dengan tabel ROW x blok dan keterangan waktu pembaruan data.

## Struktur repo

```
.
├── dashboard_parkiran.py     # dashboard Streamlit
├── hasil_v3.csv              # data yang ditampilkan dashboard
├── requirements.txt          # dependensi dashboard
├── ParkirIn_rapi.ipynb       # notebook Colab: dataset, training, evaluasi, output CSV
└── README.md
```

Foto, dataset, dan bobot model (`best.pt`) **tidak** disimpan di repo ini. Dashboard hanya membaca `hasil_v3.csv`.

## Alur kerja

```
Foto (Drive) -> Notebook Colab (YOLOv8 + kapasitas) -> hasil_v3.csv -> Dashboard Streamlit
```

1. Jalankan `ParkirIn_rapi.ipynb` di Google Colab (GPU T4) untuk menghasilkan `hasil_v3.csv`.
2. Taruh `hasil_v3.csv` di folder yang sama dengan `dashboard_parkiran.py`.
3. Jalankan dashboard.

Pembaruan data masih **manual**: dashboard tidak memproses foto sendiri.

## Menjalankan dashboard

Butuh Python 3.9 atau lebih baru.

```bash
pip install -r requirements.txt
streamlit run dashboard_parkiran.py
```

Buka `http://localhost:8501`. Data juga bisa diupload lewat sidebar dashboard tanpa menaruh CSV di folder.

Isi `requirements.txt`:

```
streamlit
pandas
tzdata
```

### Format `hasil_v3.csv`

Kolom wajib:

| Kolom | Contoh | Keterangan |
|---|---|---|
| `sesi` | `PAGI` / `MALAM` | Sesi pengambilan foto |
| `row` | `ROW1` | Baris parkir |
| `titik` | `A` | Blok A sampai F |
| `kapasitas` | `5` | Jumlah slot di blok (dihitung manual) |
| `motor_depan_v3` | `3` | Motor barisan depan yang terdeteksi model |

Kolom lain (`file`, `slot_kosong`, `status`, `waktu_update`, dll.) boleh ada. Dashboard menghitung ulang slot kosong dan status dari kolom di atas.

### Aturan status

| Status | Warna | Kondisi |
|---|---|---|
| Penuh | Merah | terisi ≥ kapasitas, atau slot kosong ≤ 1 |
| Banyak kosong | Hijau | slot kosong ≥ 50% kapasitas |
| Sebagian kosong | Kuning | selain di atas |

Zona waktu jam pembaruan diatur lewat variabel `TZ` di `dashboard_parkiran.py` (default `Asia/Jakarta`).

## Model

| | |
|---|---|
| Arsitektur | YOLOv8m (Ultralytics), bobot awal `yolov8m.pt` (COCO) |
| Kelas | `motor_depan` (satu kelas) |
| Data latih | 60 foto (ROW1-5), val 12 foto (ROW6), label dikoreksi manual di Roboflow |
| Training | 100 epoch, `imgsz=960`, `batch=8`, `freeze=10`, `lr0=0.005`, `close_mosaic=15` |
| Inference | `conf=0.45`, `iou=0.6`, `imgsz=960` |

Pembagian data dilakukan **per ROW** (bukan acak per foto) untuk menghindari kebocoran data: ROW1-5 train, ROW6 validasi, ROW7-8 uji akhir.

**Aturan label dan hitung:** hanya motor barisan depan, termasuk yang terpotong di tepi frame (kelihatan minimal ~40%), tanpa pengendara. Motor barisan belakang tidak dilabeli.

## Hasil

| Pengujian | Hasil |
|---|---|
| Validasi ROW6 (12 foto) | mAP50 0.977, precision 0.955, recall 0.929 |
| Tuning `conf` di ROW6 | MAE 0.50 pada `conf` 0.4-0.5 |
| Uji ROW7-8 (16 foto, hitungan manual) | MAE **0.81** (pagi 0.62, malam 1.00) |
| Pembanding: YOLOv8m pretrained + filter ukuran/posisi | MAE 1.00 (pagi 1.38, malam 0.62) pada foto yang sama |

MAE adalah rata-rata selisih jumlah motor per foto.

## Batasan

- **Akurasi sekitar ±1 motor per foto.** Kapasitas blok hanya 4-7 slot, jadi meleset 1 motor sudah berarti 15-25%. Baca hasil per blok sebagai status, dan hasil per ROW atau total sebagai angka yang lebih stabil.
- **Lemah di blok padat malam**, ketika motor depan berdempetan atau gelap sehingga skor deteksinya rendah (contoh ROW7A, ROW7B). Slot kosong di blok seperti itu bisa terhitung lebih banyak dari kenyataan.
- **Evaluasi kecil**: 12 foto untuk validasi dan 16 foto untuk uji, dari satu hari pengambilan data. Hasilnya belum mewakili hari hujan atau tingkat kepadatan lain.
- **Bukan real-time.** Dashboard menampilkan potret saat data terakhir dibuat.
- Hanya sampai **blok**, belum sampai nomor slot. Foto `SIDE*` dan foto bawaan HP tidak ikut karena belum punya kapasitas.
- Kapasitas blok diisi manual. Kapasitas yang keliru (misalnya ROW1A) akan membuat status blok salah.

