import csv
from pathlib import Path
import sys
import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))
import stats


def test_load_and_plot(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    hist = tmp_path / "history"
    hist.mkdir()
    csv_file = hist / "data.csv"
    with open(csv_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Azul", "2024-02-01", "100"])
        writer.writerow(["Azul", "2024-03-05", "90"])
        writer.writerow(["Latam", "2024-02-10", "80"])
    monkeypatch.chdir(tmp_path)
    counts = stats.load_data()
    assert counts["Azul"][1] == 1
    assert counts["Azul"][2] == 1
    stats.plot_heatmap(counts)
    assert Path("stats/heatmap.png").exists()
