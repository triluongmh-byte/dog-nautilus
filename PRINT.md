# In và ráp Nautilus Dog

1. **In thử trước:** `case/print/test-only.3mf`, 1 bàn, khoảng 1 giờ 28. 5 mẫu TEST ONLY.
2. **Ướm bằng đồ thật** (hướng dẫn chi tiết trong `case/README.md`, mục TEST ONLY):
   - `coupon_servo_seat`: servo đẩy vào không cần ép, lỗ vít trùng.
   - `coupon_mounts`: phích USB-C, công tắc 7 mm, mạch sạc CHG1a. Mạch hạ áp S13V30F5 (22,9×22,9 mm) **sẽ không vừa** khay hạ áp 22×17 mm. Đây là chuyện đã biết, không phải lỗi in.
   - `coupon_gear_pair`: hai bánh răng quay tay không kẹt.
   - `coupon_leg_joint`: khớp với vít M2 + đai ốc lắc tự do, hở khoảng 0,2 mm.
   - `coupon_lid`: lỗ OLED, lỗ quạt, lỗ dây, tán cấy, lỗ vít M3.
3. Mẫu nào không vừa thì ghi lại chỗ cấn và lệch bao nhiêu mm, gửi lại để sửa CAD. Chưa in bộ đủ.
4. **Đạt hết thì in bộ đủ:** `case/print/production.3mf`, 5 bàn, khoảng 4 giờ 45 (khung 1 h 55, nắp 48 phút, bánh răng 24 phút, khớp chân 1 h 04, chốt và giá 35 phút).
   - **Không dán `buck_holder`.** Dán S13V30F5 bằng băng xốp thẳng xuống sàn, góc sau-phải (cạnh sau cách vách sau ~7 mm, cạnh phải sát vách phải, không chạm khay pin). Sửa CAD khay này cần chạy lại phần vỏ trên máy có CadQuery.
   - Board bảo vệ CHG1b dán trên lưng 2 cell, dưới nắp còn khoảng 6,5 mm. Chưa kiểm trong CAD, nên đóng thử nắp trước khi bắt vít.
5. **Ráp cơ khí** theo 8 bước trong `case/README.md` / `case/overview.html`.
6. **Đấu dây** theo `engineering/harness.md`:
   - dây đỏ/nâu của servo về điểm nối ngay sau mạch hạ áp;
   - chỉ dây cam cắm chân 1 của J3 (trước-trái), J4 (trước-phải), J5 (sau-trái), J6 (sau-phải);
   - chân 2-3 của J3-J6 để trống.
7. **Bring-up** từng bước theo `engineering/bringup.md`: chưa có pin, cấp 5 V từ nguồn giới hạn dòng, rồi mới tới servo.
8. **Nạp firmware** theo `firmware/README.md`, canh pha chân ở trang `/cal`, rồi mới cho đi.
