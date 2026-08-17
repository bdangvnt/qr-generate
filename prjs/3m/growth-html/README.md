# growth-html — bản HTML để chia sẻ

Bản đọc được của kế hoạch growth, dành cho người **không mở repo**: thành viên
Nội dung, Thiết kế, đối tác, nhà đầu tư. Mở bằng trình duyệt, không cần cài gì.

| File | Cho ai | Nội dung |
|---|---|---|
| `publish.sh` | Kỹ thuật | Đồng bộ → `firebase deploy` → báo Telegram |
| `.env.deploy.example` | Kỹ thuật | Mẫu cấu hình Telegram, chép thành `.env.deploy` rồi điền |
| `growth_plan.html` | Cả nhóm | Định vị · hiện trạng · rào cản phát hành · tối ưu cửa hàng · thử nghiệm A/B · khung đo lường · mô hình doanh thu · tiêu chí dừng · thứ tự ưu tiên |

## Quan hệ với tài liệu gốc

**Markdown trong `growth/` và `docs/` là nguồn chân lý.** File HTML ở đây là bản
tổng hợp để đọc — **không sửa nội dung ở đây**. Sửa ở file gốc, rồi cập nhật lại
trang này.

Vì sao không sinh tự động từ Markdown: bản tổng hợp **cố ý không phải bản dịch
1:1**. Nó bỏ phần chi tiết thi hành (từ điển sự kiện, mẫu câu trả lời review,
bảng giả định), giữ lại phần cần cho một người muốn hiểu bức tranh trong 10 phút.
Sinh tự động sẽ cho ra một tài liệu dài không ai đọc — đúng thứ đang muốn tránh.

## Cập nhật

Khi đổi tài liệu gốc, rà lại các phần tương ứng:

| Mục trong HTML | Tài liệu gốc |
|---|---|
| §01 Định vị sản phẩm | `growth/aso.md` §1 · `docs/plan-usp.md` |
| §02 Hiện trạng triển khai | `README.md` sản phẩm · `docs/con-lai-gi.md` |
| §03 Rào cản phát hành và phạm vi ảnh hưởng | `docs/con-lai-gi.md` §1 |
| §04 Tối ưu hiển thị cửa hàng ứng dụng | `growth/aso.md` §2, §8 |
| §05 Kế hoạch thử nghiệm A/B | `growth/aso-thu-nghiem.md` |
| §06 Khung đo lường | `growth/do-luong.md` §1, §4 |
| §07 Mô hình doanh thu và đơn vị kinh tế | `docs/plan-kinh-doanh.md` §2, §6, §7, §8 |
| §08 Tiêu chí dừng và chuyển hướng | `docs/plan-kinh-doanh.md` §10 |
| §09 Thứ tự ưu tiên theo mức đòn bẩy | `docs/plan-kinh-doanh.md` §9 |

## Quy ước văn phong

Đây là **văn bản làm việc**, không phải bài viết. Ràng buộc:

- **Dùng thuật ngữ chuẩn ngành, không dùng mô tả vòng vo.** Viết "Rào cản phát
  hành và phạm vi ảnh hưởng", không viết "Việc đang chặn — và nó chặn cái gì".
- **Không khẩu ngữ**: loại bỏ *nó · mình · bạn · đừng · thôi · nhé · kiểu · cho
  vui · hẳn hoi*. Không dùng câu hỏi tu từ làm tiêu đề.
- **Không câu dẫn dắt kiểu trò chuyện.** Thay "Vì sao thứ tự này quan trọng hơn
  nó trông có vẻ" bằng "Cơ sở của thứ tự ưu tiên".
- **Mọi khẳng định phải nêu được nguồn.** Mỗi mục ghi tài liệu gốc ở dòng
  `.lead`. Số liệu mô hình phải ghi rõ là giá trị mô hình.
- **Không tự đánh giá thành tích.** Nêu trạng thái và hệ quả, không nêu nhận xét
  về chất lượng công việc đã làm.
- **Đơn vị và số liệu đặt trong ô căn phải** (`class="num"`), dùng
  `font-variant-numeric: tabular-nums`.

Trước khi chốt, quét lại bằng danh sách khẩu ngữ ở trên — lần đầu bản này viết
theo văn nói và phải viết lại toàn bộ.

## Quy ước cho file HTML thêm sau

- **Một file, tự chứa.** CSS nhúng trong `<style>`, không link ngoài, không CDN,
  không JavaScript. Gửi qua email hay chép vào USB vẫn mở được.
- **Dùng token của hệ thiết kế** (`design/README.md`): xanh ngọc `#0A6E78`, bo
  góc 12/16/20/28, đỏ chỉ dùng cho cảnh báo nghiêm trọng.
- **Hỗ trợ chế độ tối** bằng `@media (prefers-color-scheme: dark)`.
- **Bảng phải cuộn ngang được** (`.scroll`) — người đọc trên điện thoại là ca
  thường gặp, và trang không được đẩy ngang cả thân.
- **Không nhúng số liệu chưa có.** Nếu một con số là giả định thì phải ghi rõ là
  giả định — cùng luật với tài liệu gốc.

## Xuất bản

```bash
cd products/01_hoc-luat-giao-thong
./growth-html/publish.sh --dry-run   # xem sẽ làm gì
./growth-html/publish.sh             # đồng bộ → deploy → báo
```

Script thực hiện ba bước:

1. Chép `*.html` và `README.md` sang
   `/Users/dangflow/Documents/DEV/qr-generate/prjs/3m/growth-html`.
   **Chỉ chép đúng hai loại file này** — thư mục đích được publish công khai,
   nên `publish.sh` và `.env.deploy` không được lọt sang.
2. `firebase deploy --only hosting` tại `qr-generate`, dự án `an-nhien-boong`.
3. **Kiểm chứng từng đường dẫn trả về HTTP 200.** Sai đường dẫn đích thì dừng
   tại đây, không gửi tin — tránh báo "đã cập nhật" kèm một link 404.
4. Gửi tin nhắn Telegram, **kèm đường dẫn đầy đủ tới từng trang** để người nhận
   bấm là mở đúng tài liệu. Thiếu `.env.deploy` thì **bỏ qua bước này chứ không
   báo lỗi** — deploy đã hoàn tất, dừng ở đây chỉ làm người chạy hiểu nhầm.

Đường dẫn công khai được dựng từ vị trí thư mục đích so với gốc dự án Firebase
(`prjs/3m/growth-html`), nên thêm file HTML mới là tự có link, không phải sửa
script:

`https://an-nhien-boong.web.app/prjs/3m/growth-html/growth_plan.html`

> ⚠️ **Phạm vi deploy.** `firebase.json` của dự án đích khai `"public": "./"`
> kèm `rewrites: ** → /index.html`, nên **toàn bộ cây `qr-generate` được publish
> công khai**, không riêng thư mục này. Tại thời điểm dựng script điều đó bao
> gồm `prjs/3m/Phoi_hop_nhom_3_nguoi.docx` và `.xlsx` — tài liệu phối hợp nội
> bộ. Chủ sản phẩm đã được báo và chấp nhận (01/08/2026). Muốn thay đổi thì
> thêm mẫu loại trừ vào `ignore` trong `firebase.json` của dự án đích.

## Khi nào phải chạy lại

Sau **mỗi lần** sửa tài liệu kế hoạch: `docs/plan-kinh-doanh.md`,
`docs/plan-usp.md`, `docs/con-lai-gi.md`, `growth/*.md`, hoặc bảng trạng thái
trong `README.md` của sản phẩm. Cập nhật `growth_plan.html` theo bảng ánh xạ ở
trên **trước**, rồi mới chạy `publish.sh`.

