from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, CallbackContext
import logging
import re
import gspread
from google.oauth2.service_account import Credentials

# Cấu hình logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Đường dẫn đến file JSON chứa credentials
SERVICE_ACCOUNT_FILE = '/Users/apple/Desktop/TelegramBotProject/nice-aegis-416216-b0d230718611.json'

# Đường dẫn đến Google Sheet
SHEET_ID = '1azM3ZnDvXjXK6fH7qB5IaEiWFAbJJQUTtOi_LNGPtRc'

# Cấu hình Google Sheets API
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
client = gspread.authorize(credentials)
sheet = client.open_by_key(SHEET_ID).sheet1

# Hàm xử lý khi user bấm /start
async def start_or_message(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("Xem 300 bài hát thiếu nhi", callback_data='view_songs')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Hello Sếp ! Coi 300 bài hát thiếu nhi trước đi Sếp !", reply_markup=reply_markup)

# Hàm xử lý khi user chọn một trong các nút
async def button_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == 'view_songs':
        # Đọc dữ liệu từ Google Sheets
        try:
            data = sheet.get_all_values()

            if len(data) > 3:
                response = "\n".join([
                    f"{i+1}. {row[1]} / {row[3]}"
                    for i, row in enumerate(data[3:])
                    if len(row) > 6
                ])
                await query.message.reply_text(f"Danh sách bài hát:\n{response}")

                # Hỏi nếu user muốn xem chi tiết bài hát nào
                keyboard = [
                    [InlineKeyboardButton("Ok", callback_data='view_song_detail')],
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.message.reply_text("Sếp muốn coi nội dung bài nào không?", reply_markup=reply_markup)
            else:
                await query.message.reply_text("Không tìm thấy bài hát.")
        except Exception as e:
            logger.error(f"Lỗi khi đọc dữ liệu từ Google Sheets: {e}")
            await query.message.reply_text("Lỗi xảy ra khi lấy danh sách bài hát.")


    elif query.data == 'view_song_detail':
        # Hỏi số thứ tự bài hát cần xem chi tiết
        await query.message.reply_text("Bài mấy Sếp ?")
        # Lưu trạng thái để nhận số thứ tự bài hát từ người dùng
        context.user_data['waiting_for_song_number'] = True

    elif query.data == 'no_content':
        # Kết thúc tác vụ khi user bấm "Khỏi, nghỉ đi"
        await query.message.reply_text("Ok bái bai Sếp !")

    elif query.data == 'send_original_content':
        # Yêu cầu người dùng gửi bài viết gốc
        await query.message.reply_text("Sếp gửi bài gốc đi, chỗ nào cần thay nội dung sếp bỏ vô ngoặc vuông dùm em nha!")
        context.user_data['waiting_for_original_content'] = True

    elif query.data == 'viet_content_vie':
        # Bot phản hồi chờ đợi
        await query.message.reply_text("Sếp đợi em tí!")

        # Thay thế nội dung trong ngoặc vuông bằng nội dung Tiếng Việt (content_vie)
        original_content = context.user_data.get('original_content', '')
        song_number = context.user_data.get('song_number', -1)

        if song_number != -1:
            data = sheet.get_all_values()
            content_vie = data[song_number + 2][7]  # Lấy nội dung từ cột H

            # Thay thế đoạn văn trong ngoặc vuông bằng nội dung Tiếng Việt
            updated_content = re.sub(r'\[.*?\]', content_vie, original_content)

            # Trả kết quả cho người dùng
            await query.message.reply_text(f"\n\n{updated_content}")
        else:
            await query.message.reply_text("Lỗi: Không tìm thấy số thứ tự bài hát.")

    elif query.data == 'viet_content_eng':
        # Bot phản hồi chờ đợi
        await query.message.reply_text("Wait...")

        # Thay thế nội dung trong ngoặc vuông bằng nội dung English (content_eng)
        original_content = context.user_data.get('original_content', '')
        song_number = context.user_data.get('song_number', -1)

        if song_number != -1:
            data = sheet.get_all_values()
            content_eng = data[song_number + 2][8]  # Lấy nội dung từ cột I

            # Thay thế đoạn văn trong ngoặc vuông bằng nội dung English
            updated_content = re.sub(r'\[.*?\]', content_eng, original_content)

            # Trả kết quả cho người dùng
            await query.message.reply_text(f"\n\n{updated_content}")
        else:
            await query.message.reply_text("Error: Song number not found.")

# Hàm kiểm tra nội dung có nằm trong ngoặc vuông không
def contains_square_brackets(text: str) -> bool:
    # Sử dụng regex để kiểm tra đoạn văn nằm trong ngoặc vuông
    return bool(re.search(r'\[.*?\]', text))

# Hàm xử lý khi nhận tin nhắn từ người dùng
async def handle_message(update: Update, context: CallbackContext) -> None:
    if context.user_data.get('waiting_for_song_number'):
        try:
            # Nhận số thứ tự bài hát từ tin nhắn của người dùng
            song_number = int(update.message.text.strip())
            context.user_data['song_number'] = song_number  # Lưu lại số bài hát

            # Đọc dữ liệu từ Google Sheets
            data = sheet.get_all_values()

            if len(data) > 3 and 0 < song_number <= len(data) - 3:
                row = data[song_number + 2]  # Số thứ tự bắt đầu từ 1, cộng thêm 2 để lấy dữ liệu đúng hàng
                content_vie = row[7]  # Cột H - Tiếng Việt
                content_eng = row[8]  # Cột I - English
                content_flavor = row[6] # Cột G - Mùi vị
                await update.message.reply_text(f"Mùi vị : {content_flavor}")
                await update.message.reply_text(f"{content_vie}")
                await update.message.reply_text(f"{content_eng}")

                # Sau khi trả kết quả bài hát, hỏi nếu người dùng muốn viết content mới
                keyboard = [
                    [InlineKeyboardButton("Gửi bài viết gốc", callback_data='send_original_content')],
                    [InlineKeyboardButton("Khỏi, nghỉ đi cậu", callback_data='no_content')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text("Sếp muốn viết content mới không?", reply_markup=reply_markup)

            else:
                await update.message.reply_text("Số thứ tự bài hát không hợp lệ. Vui lòng nhập lại.")
        except ValueError:
            await update.message.reply_text("Vui lòng nhập một số hợp lệ.")
        except Exception as e:
            logger.error(f"Lỗi khi xử lý số thứ tự bài hát: {e}")
            await update.message.reply_text("Lỗi xảy ra khi tìm kiếm bài hát.")

        # Xóa trạng thái sau khi nhận được số bài hát
        context.user_data['waiting_for_song_number'] = False

    elif context.user_data.get('waiting_for_original_content'):
        # Nhận bài viết gốc từ người dùng
        original_content = update.message.text
        context.user_data['original_content'] = original_content  # Lưu lại bài viết gốc

        # Kiểm tra xem nội dung có nằm trong ngoặc vuông hay không
        if contains_square_brackets(original_content):
            # Hỏi xem người dùng muốn viết bài Tiếng Việt hay English
            keyboard = [
                [InlineKeyboardButton("Tiếng Việt", callback_data='viet_content_vie')],
                [InlineKeyboardButton("English", callback_data='viet_content_eng')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("Sếp viết bài tiếng Việt hay tiếng Anh?", reply_markup=reply_markup)

            # Xóa trạng thái sau khi nhận được bài viết gốc hợp lệ
            context.user_data['waiting_for_original_content'] = False
        else:
            # Yêu cầu user nhập lại nội dung có chứa ngoặc vuông
            await update.message.reply_text("Sếp check lại chỗ cần đổi bỏ vô ngoặc vuông chưa Sếp 😅")

        
# Hàm xử lý lỗi
async def error_handler(update: object, context: CallbackContext) -> None:
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

# Hàm main khởi chạy bot
def main() -> None:
    application = Application.builder().token("7527402100:AAF9UwVZNOi0NQTKkmMAROuMP-V7PJD_F4A").build()

    # Thêm các handler vào bot
    application.add_handler(CommandHandler("start", start_or_message))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_handler))

    # Thêm handler xử lý lỗi
    application.add_error_handler(error_handler)

    # Chạy bot
    application.run_polling()

if __name__ == '__main__':
    main()
