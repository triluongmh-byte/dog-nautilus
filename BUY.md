# Danh sách mua để ráp Nautilus Dog

Nguồn số liệu: `parts.json`, `case/hardware.json`, `engineering/harness.md`. Mã/kích thước ghi "GIẢ ĐỊNH" là chưa đo trên hàng thật.
Mua theo thứ tự: **nhóm A** đủ để in thử và ướm (mục 1 của PRINT.md); **nhóm B** để ráp điện; **nhóm C** pin, chỉ lắp sau khi kiểm mạch sạc.

## A. Ướm mẫu in thử và ráp cơ khí
| Món | Số lượng | Ghi chú |
|---|---|---|
| Nhựa PETG 1,75 mm | 1 cuộn (1 kg) | Profile in đang GIẢ ĐỊNH Bambu A1, đầu 0,4 mm |
| Vít M2×18 | 4 | khớp C (1 con/chân) |
| Vít M2×14 | 12 | khớp D, E, F (3 con/chân) |
| Vít M2×8 | 4 | khớp G |
| Đai ốc lục giác M2 | 20 + 8 = 28 | 20 cho chân, 8 cho OLED |
| Vít M2×10 | 4 | bắt OLED |
| Vít tự ren M2×5 | 4 | bắt tấm mạch vào 4 trụ; GIẢ ĐỊNH lỗ mồi 1,6 mm sâu ~4 mm |
| Vít tự ren M3×10 đầu tròn | 4 | đóng nắp |
| Tán cấy nhiệt M3×4 (OD ~4,6) | 8 | trụ mở rộng trên nắp |
| Vít M3×16 + đai ốc M3 | 4 + 4 | bắt quạt |
| Keo 502 (CA) | 1 tuýp | |
| Băng keo xốp 2 mặt | 1 cuộn | dán mạch hạ áp, mạch sạc, board bảo vệ |
| Servo quay liên tục SG90/FS90R | 0 (đã có 8) | dùng 4, giữ 4 dự phòng |

## B. Điện tử
| Món | Số lượng | Ghi chú |
|---|---|---|
| ESP32-C3 SuperMini | 2 | 1 dự phòng; đối chiếu chữ in trên board với `engineering/pinout.md` |
| OLED 1,54" 128×64 SSD1309, **bản I2C 4 chân** | 1 | nhiều bản bán mặc định SPI 7 chân; chọn bản ghi rõ I2C |
| Pololu S13V30F5 (5 V 3 A tăng/giảm áp) | 1 | 22,9×22,9 mm: **không vừa hộp giữ in sẵn**, dán băng xốp xuống sàn (PRINT.md) |
| Mạch sạc USB-C 2S có chân cân bằng BM (CHG1a) | 1 | ra 8,4 V; đo áp ra trước khi nối cell |
| Board bảo vệ 2S HX-2S-JH20 10 A (CHG1b) | 1 | chân B+/BM/B-/P+/P- |
| Cầu chì tự phục hồi (PTC) giữ ~4 A | 1 | trên dây P+ → công tắc |
| Công tắc lỗ 7 mm, chịu ≥3 A DC | 1 | GIẢ ĐỊNH; ướm bằng `coupon_mounts` |
| Quạt 30×30 mm 5 V | 1 | 2 dây đỏ/đen |
| Tấm đục lỗ 2,54 mm | 1 | cắt 22×52 mm, khoan 4 lỗ 2,2 mm như board KiCad |
| Điện trở 1/4 W: 4,7k / 100k / 33k / 10k | 2 / 1 / 1 / 4 | R1-R2 / R3 / R4 / R5-R8 |
| Tụ gốm 100 nF | 3 | C2-C4 |
| Tụ hóa 1000 µF 10 V (8×11,5 mm) | 1 | C1, ví dụ Rubycon 10PX1000MEFC8X11.5 |
| Tụ hóa 220 µF 10 V | 1 | dự phòng, chỉ hàn nếu ESP32 reset khi servo chạy (bringup bước 6) |
| Diode 1N5817 | 1 | D1 (hoặc SS14) |
| Thanh header đực 2,54 mm 40 chân | 2 | J1-J9 và 2 hàng 8 chân cho ESP32 |
| Vỏ Dupont cái 1 chân + đầu cos | 10 | 4 dây tín hiệu servo + dự phòng |
| Vỏ Dupont cái 2/4/6 chân thấp | mỗi loại 2 | J1/J2/J8, J7, J9 |
| Dây AWG24 đỏ, đen, cam | mỗi màu 2 m | |
| Ống co nhiệt 2-3 mm | 1 bộ | |
| Cáp USB-C dữ liệu | 1 | nạp firmware |

## C. Pin (chỉ lắp sau khi kiểm mạch sạc)
| Món | Số lượng | Ghi chú |
|---|---|---|
| Cell 18650 **không mạch bảo vệ**, dài 65 mm, xả ≥5 A liên tục | 2 | cùng loại, cùng lô, ví dụ Samsung INR18650-25R; cell có mạch bảo vệ dài tới 69 mm sẽ không vừa |
| Kẽm hàn pin (nickel strip) | 1 đoạn 20 cm | nên nhờ tiệm hàn bấm pin, không hàn mỏ trực tiếp lên cell |

## Dụng cụ
Mỏ hàn và thiếc, đồng hồ vạn năng, máy in 3D, kìm tuốt dây, kìm bấm cos Dupont, súng nhiệt hoặc bật lửa cho co nhiệt, mỏ hàn đầu cấy tán nhiệt (hoặc mỏ hàn thường ~220 °C).
