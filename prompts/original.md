# Robot Chó Nautilus V0

Làm một con robot chó đồ chơi 4 chân, đi bộ được, điều khiển bằng điện thoại.

## Cơ chế (quan trọng nhất)
- Mỗi chân chạy bằng **1 servo quay liên tục 360°** (cỡ SG90/FS90R, user có sẵn 8 con, dùng 4, 4 con dự phòng).
- Servo quay **cặp bánh răng nautilus** (xoắn ốc, quay 1:1 nhưng tốc độ lúc nhanh lúc chậm), bánh crank kéo **chân kiểu Jansen** → bàn chân bước đáy phẳng. Xem `/Users/macbookpro/harnesses/prompts/ROBOT-DOG-NAUTILUS-V0-refs/mechanism-reference.png`.
- Chân trước vươn ra trước, chân sau vươn ra sau, 4 bàn chân sát 4 góc thân cho đứng vững.

## Bản nháp có sẵn
- User đã vẽ nháp bằng cadsmith, qua kiểm tường mỏng/khe hở: `/Users/macbookpro/harnesses/prompts/ROBOT-DOG-NAUTILUS-V0-refs/cadsmith-draft-model.py` (CadQuery, đọc docstring đầu file) và bản vẽ `drawing-assembly.svg`, `drawing.frame.svg`, `drawing.lid.svg`.
- Dùng làm điểm xuất phát cho case, KHÔNG coi là đã in/đã thử. Đổi gì so với nháp thì ghi lý do.

## Kích thước & in
- Thân hộp (khung + nắp) **126 × 75 × 31 mm**; cả con khoảng 126 × 150 × 70 mm.
- Ít part, ít vít; khớp chân dùng vít M2 + tán; nắp bắt vít tự ren.
- Nắp có: lỗ màn OLED 1.54" nằm ngang phía trước, lỗ quạt 30×30 (4 lỗ cách 23 mm) phía sau, **bộ trụ mở rộng giữa nắp** cho module sau này (camera, tay robot) + lỗ luồn dây.
- Vách sau: lỗ USB rộng (24 × 18) + lỗ công tắc.
- Chỗ yếu đã biết từ bản nháp, cần xử lý: vách trên lỗ servo chỉ ~1 mm, khung cần nhiều support dưới các trụ trục chìa ngang.
- Phải có bài in thử nhỏ (TEST ONLY / MATING_TEST: ổ servo, cặp bánh răng, 1 khớp chân) trước khi in đủ bộ.

## Điện (ưu tiên module có sẵn, hàn dây tay, không cần đặt mạch)
- Board **ESP32-C3 SuperMini**; 2 cell 18650 (2S) + mạch sạc/bảo vệ 2S ra lỗ USB vách sau + công tắc; hạ áp 5–6 V ≥3 A cho servo + quạt; tụ 1000 µF đường servo.
- Màn OLED 1.54" 128×64 (I2C) hiện mặt cười / trạng thái pin.
- Quạt 30×30 5 V hút gió ra.
- Chừa sẵn đầu cắm 5V/GND/I2C/2 GPIO gần lỗ luồn dây cho module sau.
- Board KiCad chỉ là board giả/sơ đồ để kiểm ERC, không đặt hàng.

## Điều khiển
- Bật lên phát Wi-Fi, màn hiện mã QR để điện thoại vào trang điều khiển.
- Trang web: đi tới/lùi/trái/phải/đứng, chỉnh tốc độ, kiểu đi (trot), hiện % pin.
- Servo 360 không biết góc: có bước canh pha chân bằng tay trong trang web (nút xoay từng chân từng chút).

## Không làm
- Không tự nạp firmware, không chạy motor, không in, không đặt hàng.