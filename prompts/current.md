# Robot Chó Nautilus V0

Robot đồ chơi bốn chân: mỗi chân một servo quay liên tục → cặp bánh răng nautilus → chân Jansen. Có 8 servo, dùng 4 và để 4 dự phòng. Khung+nắp 126 × 75 × 31 mm; chân trước vươn trước, chân sau vươn sau. Điện hàn dây tay: ESP32-C3 SuperMini, 2S 18650 với module sạc/bảo vệ, buck 5 V ≥3 A, tụ 1000 µF, OLED I2C 1.54 inch 128×64, quạt 30×30 và đầu mở rộng. KiCad chỉ ghi sơ đồ/ERC, không đặt hàng.

Điện thoại qua Wi-Fi AP/QR: tới/lùi/rẽ/dừng, tốc độ, trot, % pin ước lượng và canh pha từng chân. Nắp có OLED trước, quạt sau, trụ mở rộng/lỗ dây giữa. Vách sau USB 24×18 và công tắc. TEST ONLY ổ servo, cặp bánh răng và khớp chân phải có trước bộ đầy đủ. Không tự nạp, chạy motor, in hoặc đặt hàng.

[Đề bài nguyên văn](original.md) · [Tham chiếu](assets/REFERENCES.md) · [Trạng thái và giới hạn](../README.md)

Trạng thái ngày 2026-11-12: harness báo teamReady=true; native ERC/DRC/parity 0 finding, firmware đã biên dịch ESP32-C3. CAD có đủ khung, nắp, bốn cụm chân và trục; quét 72 tư thế đã qua. Bao quỹ đạo khoảng 152,1 × 144,6 × 69,6 mm. Bộ in có 47 chi tiết/5 plate và 5 mẫu TEST ONLY riêng; chưa in/thử thật.

Còn giới hạn bàn giao: PrintTeam thử hai lần đều lỗi do kế hoạch plate 0/danh sách rỗng dù bộ đọc nhận đủ 5 plate; manufacturing còn 3 lỗi bằng chứng cũ; 3D/GUI chưa xác nhận vì WebGL/cửa sổ UI không khả dụng. Manifest overview, mesh tham chiếu và một số metadata/hướng dẫn còn cần đội case/điện đồng bộ, có danh sách trong README. Các cờ đạt trong mô hình không chứng minh robot đã đi được trên phần cứng.
