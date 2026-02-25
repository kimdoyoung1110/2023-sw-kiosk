from tkinter import *
from tkinter import ttk, simpledialog
import tkinter.messagebox as msgbox
from datetime import datetime
import csv
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

canvas = None
scrollbar = None

def on_hover(event):
    # 아무런 동작 없이 무시하도록 설정
    pass

def on_mousewheel(event):
    canvas.yview_scroll(int(-1*(event.delta/120)), "units")

def scroll_to_recommand():
    canvas.yview_moveto(0)  

def scroll_to_main():
    canvas.yview_moveto(0.23)

def scroll_to_an_ju():
    canvas.yview_moveto(0.6)  

def scroll_to_alco():
    canvas.yview_moveto(1)

def info():
    msgbox.showinfo("알림", "직원이 호출되었습니다. 잠시만 기다려주세요.")

def remove_item_from_cart(menu_name):
    existing_labels = cart_content_frame.winfo_children()

    for frame in existing_labels:
        try:
            label = frame.grid_slaves(row=0, column=0)[0]
            current_quantity = int(frame.grid_slaves(row=0, column=2)[0].cget("text"))
        except IndexError:
            continue
        except ValueError:
            continue

        if label["text"].startswith(menu_name):
            if current_quantity > 1:
                frame.grid_slaves(row=0, column=2)[0].config(text=str(current_quantity - 1))
            else:
                frame.destroy()  # 수량이 0이 되면 프레임을 삭제

            update_total_price()
            break  # 함수 종료


# 메뉴가 추가되는 그리드 아래에 새로운 메뉴를 장바구니에 추가한 후 총 합 업데이트
def add_to_cart(menu_name, price, quantity_var):
    menu_info = f"{menu_name}\n{price}원"
    existing_labels = cart_content_frame.winfo_children()

    # 이미 장바구니에 추가된 메뉴인지 확인
    for frame in existing_labels:
        try:
            label = frame.grid_slaves(row=0, column=0)[0]
            current_quantity = int(frame.grid_slaves(row=0, column=2)[0].cget("text"))
        except IndexError:
            continue
        except ValueError:
            continue

        if label["text"].startswith(menu_name):
            try:
                frame.grid_slaves(row=0, column=2)[0].config(text=str(current_quantity + 1))
            except TclError:
                continue
            else:
                # 메뉴가 이미 추가된 경우 총 합 업데이트 후 함수 종료
                update_total_price()
                return

    # 메뉴가 추가되지 않은 경우 새로운 프레임 생성
    try:
        menu_frame = Frame(cart_content_frame, bg="white")
        menu_frame.grid(row=cart_content_frame.grid_size()[1], column=0, sticky='w')

        menu_label = Label(menu_frame, text=menu_info, fg='black', bg="white", pady=5, font=('Malgun Gothic', 12))
        menu_label.grid(row=0, column=0, sticky='w')

        decrease_button = Button(menu_frame, text="-", command=lambda frame=menu_frame: decrease_quantity(frame))
        decrease_button.grid(row=0, column=1, sticky='e')

        quantity_label = Label(menu_frame, text="1", font=('Malgun Gothic', 12), padx=5, pady=5, bg="white")
        quantity_label.grid(row=0, column=2)

        increase_button = Button(menu_frame, text="+", command=lambda frame=menu_frame: increase_quantity(frame))
        increase_button.grid(row=0, column=3, sticky='e')

        # 메뉴가 추가된 후 스크롤 업데이트
        update_scroll()

    except TclError:
        return

    # 새로운 메뉴를 장바구니에 추가한 후 총 합 업데이트
    update_total_price()

# 감소 및 증가 버튼 클릭 시 총 합 업데이트
def increase_quantity(frame):
    current_quantity = int(frame.grid_slaves(row=0, column=2)[0].cget("text"))
    frame.grid_slaves(row=0, column=2)[0].config(text=str(current_quantity + 1))
    update_total_price()

def decrease_quantity(frame):
    current_quantity = int(frame.grid_slaves(row=0, column=2)[0].cget("text"))
    if current_quantity > 1:
        frame.grid_slaves(row=0, column=2)[0].config(text=str(current_quantity - 1))
    else:
        menu_name = frame.grid_slaves(row=0, column=0)[0].cget("text").split("\n")[0]
        remove_item_from_cart(menu_name)  # 수량이 0이 되면 해당 메뉴를 장바구니에서 삭제

    update_total_price()



# 주문 내역 창에 대한 클래스 정의
class OrderHistoryWindow(Toplevel):
    order_history_window = None

    def __init__(self, master, order_history_list):
        super().__init__(master)
        self.title("주문 내역")
        self.geometry("400x450")
        self.order_label = Label(self, text="주문내역", font=('Malgun Gothic', 14, 'bold'))
        self.order_label.pack(side='top')
        self.order_listbox = Listbox(self, width=50, height=15, font=('Malgun Gothic', 12, 'bold'))
        

        self.total_price = 0  # 전체 주문 가격 초기화

        for order in order_history_list:
            self.order_listbox.insert(END, f"{order['메뉴이름']} X {order['수량']}       {order['가격']}원")
            self.total_price += order['가격']  # 주문 가격 누적

        self.order_listbox.pack(pady=10)

        # 총 가격 표시 레이블
        total_label = Label(self, text=f"총 가격: {self.total_price}원", font=('Malgun Gothic', 12, 'bold'))
        total_label.pack(pady=10)

    def destroy_window(self):
        # 창이 닫힐 때 호출되는 메서드
        OrderHistoryWindow.order_history_window = None
        self.destroy()


# 주문 내역 리스트를 저장할 리스트
order_history_list = []
order_history_window = None  # 주문 내역 창 객체

# 결제 완료 후 장바구니 비우기
def clear_cart():
    existing_labels = cart_content_frame.winfo_children()
    for widget in existing_labels:
        widget.destroy()
    total_price_label.config(text="총 가격: 0원")

# 주문 내역을 보여주는 함수
def show_order_history():
    global order_history_list
    global order_history_window
    if order_history_list:  # 주문 내역이 있을 때만 창 열기
        # 주문 내역 창이 이미 열려 있다면 닫고, 아니면 새로 생성
        if OrderHistoryWindow.order_history_window:
            OrderHistoryWindow.order_history_window.destroy_window()  # 창 닫기
        OrderHistoryWindow.order_history_window = OrderHistoryWindow(root, order_history_list)

        # 결제 완료 후 장바구니 비우기
        clear_cart()

# 주문 저장 및 csv 파일에 저장하는 부분
def save_order_to_csv():
    global order_history_list

    # 현재 시간을 얻어옴
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        with open("order.csv", 'a', newline='', encoding='utf-8') as csvfile:
            csv_writer = csv.writer(csvfile)

            existing_labels = cart_content_frame.winfo_children()
            for frame in existing_labels:
                try:
                    menu_info = frame.grid_slaves(row=0, column=0)[0].cget("text")
                    price_str = menu_info.split("\n")[-1]
                    unit_price = int(''.join(filter(str.isdigit, price_str)))
                    quantity = int(frame.grid_slaves(row=0, column=2)[0].cget("text"))
                    menu_name = menu_info.split("\n")[0]

                    # 이미 주문 내역에 메뉴가 있는지 확인
                    existing_menu = next((item for item in order_history_list if item['메뉴이름'] == menu_name), None)

                    if existing_menu:
                        # 이미 주문 내역에 있는 경우 수량만 증가
                        existing_menu['수량'] += quantity
                        existing_menu['가격'] += unit_price * quantity  # 가격 갱신
                    else:
                        # 주문 내역에 추가
                        total_price = unit_price * quantity
                        csv_writer.writerow([current_time, menu_name, quantity, total_price])
                        order_history_list.append({
                            '메뉴이름': menu_name,
                            '수량': quantity,
                            '가격': total_price
                        })

                except (IndexError, ValueError):
                    continue

        msgbox.showinfo("알림", "주문이 완료되었습니다.")

        # 주문 내역 창 업데이트
        show_order_history()

        # 결제 완료 후 장바구니 비우기
        clear_cart()

    except Exception as e:
        msgbox.showerror("오류", f"주문이 완료되지 못하였습니다. 다시 시도하여 주십시오.: {str(e)}")

def set_korean_font():
    plt.rcParams['font.family']='Malgun Gothic' # Windows(전체 폰트 설정)
    # plt.rcParams['font.family']='AppleGothic' # Mac
    plt.rcParams['font.size']=10 # 글자크기
    plt.rcParams['axes.unicode_minus']=False # 한글 폰트 사용 시, 마이너스 글자가 깨지는 현상 해결

def show_setting():
    password = simpledialog.askstring("비밀번호 입력", "비밀번호를 입력하세요:", show='*')
    # 날짜 생성
    dates = pd.date_range(start='2023-12-01 17:00:00', end='2023-12-31 01:00:00', freq='H')

    # 랜덤 데이터 생성
    np.random.seed(42)
    data = {
        '시간': np.random.choice(dates, size=1000),
        '메뉴': np.random.choice(['탁탁후라이드치킨', '곱창탁전골', '돼지탁탁불백', '골뱅이탁탁무침', '국물탁발', '해장탁라면',
                                '탁탁해물파전', '반건조탁징어', '두부김치', '탁막걸리', '참이슬', '카스'], size=1000),
        '수량': np.random.randint(1, 10, size=1000),
        '가격': np.random.randint(5000, 15000, size=1000)
    }

    df = pd.DataFrame(data)

    # 영업시간에 해당하는 데이터만 선택
    df = df[(df['시간'].dt.hour >= 17) | (df['시간'].dt.hour <= 1)]

    # 비번 확인
    if password == "1234":
        # 키오스크 종료 함수
        def close_root():
            root.destroy()

        def plot_graph(graph_type, df):
            set_korean_font()  # 한글 폰트 설정

            # Add '매출액' column to the DataFrame
            df['매출액'] = df['수량'] * df['가격']

            # 1번째 그래프
            if graph_type == '기간별 판매량 확인하기':
                fig, ax1 = plt.subplots(figsize=(15, 6))
                # Resample data to daily frequency
                daily_sales = df.resample('D', on='시간').agg({'수량': 'sum', '매출액': 'sum'})
                color = 'tab:red'
                ax1.set_xlabel('날짜')
                ax1.set_ylabel('매출액 (만 원)', color=color)
                ax1.bar(daily_sales.index, daily_sales['매출액'] / 10000, color=color)
                ax1.tick_params(axis='y', labelcolor=color)
                ax1.set_xticks(daily_sales.index)
                ax1.set_xticklabels(daily_sales.index.strftime('%m-%d'), rotation=45, ha='right')
                for i, value in enumerate(daily_sales['매출액']):
                    ax1.text(daily_sales.index[i], value / 10000, f'{value // 10000}만', ha='center', va='bottom')
                ax1.plot(daily_sales.index, daily_sales['매출액'] / 10000, marker='o', markersize=8, color='black',
                        linestyle='-', linewidth=2)
                fig.tight_layout()
                plt.title('기간별 매출액')
                plt.show()


            elif graph_type == '자리별 산점도 확인하기':
                table_numbers = np.random.choice([1, 1, 1, 2, 3, 4, 5, 5, 5, 6, 7, 8, 9, 9, 9, 10, 11, 12, 13, 13, 13, 14, 15, 16], size=len(df))
                df['테이블번호'] = table_numbers

                fig, ax = plt.subplots(figsize=(12, 8))

                scatter = ax.scatter(df.index, df['테이블번호'], c=df['수량'], cmap='viridis', s=df['수량'] * 20, alpha=0.7)
                plt.colorbar(scatter, label='수량')

                ax.set_title('자리별 산점도')
                ax.set_xlabel('시간')
                ax.set_ylabel('테이블 번호')

                ax.set_yticks(np.arange(1, 17))  # y축에 1부터 16까지 표시
                plt.show()

            elif graph_type == '메뉴별 판매량 확인하기':
                menu_types = [['탁탁후라이드치킨', '곱창탁전골', '돼지탁탁불백', '골뱅이탁탁무침', '국물탁발', '해장탁라면'],
                            ['탁탁해물파전', '반건조탁징어', '두부김치'],
                            ['탁막걸리', '참이슬', '카스']]

                fig, ax = plt.subplots(figsize=(15, 8))  # 그래프 크기 조정

                # 색상 구성
                colors = plt.cm.viridis(np.linspace(0, 1, len(df['메뉴'].unique())))

                for i, menu_type in enumerate(menu_types):
                    menu_sales = df[df['메뉴'].isin(menu_type)].groupby('메뉴').agg({'수량': 'sum', '매출액': 'sum'})
                    ax.bar(menu_sales.index, menu_sales['수량'], color=colors[i], label=f'{menu_type[0]} 등 {len(menu_type)}개 메뉴')

                    # 각 막대 위에 판매량 표시
                    for x, y in zip(menu_sales.index, menu_sales['수량']):
                        ax.text(x, y, f'{y}', ha='center', va='bottom')

                ax.set_ylabel('수량')
                ax.set_title('메뉴별 판매량')
                ax.legend()
                plt.xticks(rotation=45, ha='right')  # 메뉴명을 45도 회전하여 표시
                plt.show()

            elif graph_type == '시간별 판매량 확인하기':
                df = pd.read_csv('sales.csv', encoding='cp949')
                timedata = df.iloc[10,3::3]
                labels = ['17시','18시','19시','20시','21시','22시','23시','24시']
                wedgeprops={'width': 0.3, 'edgecolor': 'black', 'linewidth': 2}
                # 면적이 작아서 %표시 안하고 싶을때
                def custom_autopct(pct):
                    if pct >= 10:
                        return '{:.1f}%'.format(pct)
                    else:
                        return ''
                plt.title('시간별 판매량')
                plt.pie(timedata, labels=labels, autopct=custom_autopct, startangle=90, counterclock=False, wedgeprops=wedgeprops, pctdistance=0.5)
                plt.legend(loc=(1.1, 0.1))
                plt.show()

        msgbox.showinfo("알림", "비밀번호가 확인되었습니다. 관리자 창을 띄웁니다.")

        # 새로운 창 생성
        settings_window = Toplevel(root)
        settings_window.title("관리자 창")
        settings_window.geometry("1100x640")
        settings_window.resizable(False, False)

        # 배경 색 변경
        settings_window.configure(bg='#686666')

        # 메인 로고
        main_frame = Frame(settings_window, relief='solid', bd=0)
        main_frame.grid(row=0, column=1, pady=20)
        main_frame.configure(bg='#686666')
        main_label = Label(main_frame, text='아래 버튼을 클릭하여 매출을 확인해보세요!', font=('Malgun Gothic', 16, 'bold'), bg='#686666', fg='white')
        main_label.pack()

        # 그래프 frame
        graphe_frame = Frame(settings_window, relief='solid', bd=0)
        graphe_frame.grid(row=1, column=1, pady=100, padx=50)
        graphe_frame.configure(bg='#686666')

        # 그래프 frame 안 버튼
        sales_per_mth_btn = Button(graphe_frame, text='기간별 판매량 확인하기', font=('Malgun Gothic', 14, 'bold'), command=lambda: plot_graph('기간별 판매량 확인하기', df))
        spot_scatter_btn = Button(graphe_frame, text='자리별 산점도 확인하기', font=('Malgun Gothic', 14, 'bold'), command=lambda: plot_graph('자리별 산점도 확인하기', df))
        sales_per_menu_btn = Button(graphe_frame, text='메뉴별 판매량 확인하기', font=('Malgun Gothic', 14, 'bold'), command=lambda: plot_graph('메뉴별 판매량 확인하기', df))
        sales_per_hour_btn = Button(graphe_frame, text='시간별 판매량 확인하기', font=('Malgun Gothic', 14, 'bold'), command=lambda: plot_graph('시간별 판매량 확인하기', df))

        # 전원버튼
        off_root_btn = Button(settings_window, text="키오스크 및 관리자 창 종료", command=close_root, font=('Malgun Gothic', 12, 'bold'))
        off_root_btn.grid(row=2, column=1, pady=20)

        # 버튼 배치
        sales_per_mth_btn.grid(row=0, column=0, padx=10)
        spot_scatter_btn.grid(row=0, column=1, padx=10)
        sales_per_menu_btn.grid(row=0, column=2, padx=10)
        sales_per_hour_btn.grid(row=0, column=3, padx=10)


    else:
        msgbox.showerror("오류", "비밀번호가 일치하지 않습니다.")


root = Tk()
root.title("메뉴")
root.geometry("1100x640")  # 전체 너비를 늘려주었습니다.fw
root.resizable(False, False) 

# 스타일 설정
style = ttk.Style()

# 결제하기 버튼 스타일
style.theme_use('alt')
style.configure('TButton.Payment.TButton', font=('Malgun Gothic', 12, 'bold'), width=15, height=2, background="#088A29", foreground="white")
style.map('TButton.Payment.TButton', background=[('active', '#088A29')])

# 각 열의 너비를 설정
for i in range(5):  # 5열로 변경
    root.columnconfigure(i, weight=1)  # 각 열 (고정 너비)

# 각 행의 높이를 설정
for i in range(6):  # 전체 6행
    root.rowconfigure(i, weight=1)  # 각 행 (비율에 따라 조정)

# 메인 로고 프레임
main_logo_frame = ttk.Frame(root, relief='solid', style='TFrame', padding=(1, 1, 1, 1))
main_logo_frame.grid(row=0, column=0, columnspan=5, sticky='nsew')  # sticky를 'nsew'로 설정하고, columnspan 추가

main_logo = PhotoImage(file='./img/main_logo_gray.png')
main_logo = main_logo.subsample(7, 7) 

style = ttk.Style()
style.configure('TFrame', borderwidth=1, relief='solid', background='#686666')

cart_style = ttk.Style()
cart_style.configure('CFrame.TFrame', borderwidth=1, relief='solid', background='white')

main_logo_label = Label(main_logo_frame, image=main_logo, bg='#686666')
main_logo_label.pack(side='left')

# 메인 로고 label의 크기를 조절하여 메인 로고 프레임의 높이를 동적으로 변경
main_logo_label.config(height=80)

# 왼쪽에 메뉴 버튼들이 출력될 프레임
menu_buttons_frame = Frame(root, bg="#4F4E4E")
menu_buttons_frame.grid(row=1, column=0, sticky='nsew', rowspan=5, columnspan=1)  # sticky를 'nsew'로 설정

# Set the row configuration for all rows in menu_buttons_frame
for i in range(4):  # Update to 4 rows
    menu_buttons_frame.rowconfigure(i, weight=1)  # 행의 너비를 설정

# 가운데 정렬을 위해 추가
menu_buttons_frame.columnconfigure(0, weight=1)  # 버튼이 센터에 위치하도록 설정

# 각각의 메뉴 버튼 생성 및 추가
menu_button_recommend = Button(menu_buttons_frame, text="추천메뉴", command=scroll_to_recommand, bg='#313131', fg='white', font=('Malgun Gothic', 14, 'bold'))
menu_button_main = Button(menu_buttons_frame, text="메인메뉴", command=scroll_to_main, bg='#313131', fg='white', font=('Malgun Gothic', 14, 'bold'))
menu_button_appetizer = Button(menu_buttons_frame, text="안주", command=scroll_to_an_ju, bg='#313131', fg='white', font=('Malgun Gothic', 14, 'bold'))
menu_button_drink = Button(menu_buttons_frame, text="주류", command=scroll_to_alco, bg='#313131', fg='white', font=('Malgun Gothic', 14, 'bold'))

# 버튼에 호버 이벤트 설정
menu_button_recommend.bind("<Enter>", on_hover)
menu_button_main.bind("<Enter>", on_hover)
menu_button_appetizer.bind("<Enter>", on_hover)
menu_button_drink.bind("<Enter>", on_hover)

menu_button_recommend.grid(row=0, column=0, sticky='nsew', pady=10, padx=5)
menu_button_main.grid(row=1, column=0, sticky='nsew', pady=10, padx=5)
menu_button_appetizer.grid(row=2, column=0, sticky='nsew', pady=10, padx=5)
menu_button_drink.grid(row=3, column=0, sticky='nsew', pady=10, padx=5)

# 장바구니 프레임
cart_frame = ttk.Frame(root, relief='solid', style='CFrame.TFrame', padding=(1, 1, 1, 1))
cart_frame.grid(row=0, column=4, rowspan=7, columnspan=1, sticky='nsew')  # sticky를 'nsew'로 설정

# 결제하기 버튼 위에 총 합을 표시할 레이블
total_price_label = Label(cart_frame, text="총 합: 0원", font=('Malgun Gothic', 12, 'bold'), bg="white")
total_price_label.pack(side='top', pady=(10, 0))  # 상단에 위치하며 아래쪽으로 일정 간격을 두기 위해 pady 추가

# 총 합 업데이트 함수
def update_total_price():
    total_price = 0
    existing_labels = cart_content_frame.winfo_children()
    for frame in existing_labels:
        try:
            menu_info = frame.grid_slaves(row=0, column=0)[0].cget("text")
            price_str = menu_info.split("\n")[-1]  # 메뉴 정보에서 가격 부분을 추출
            price = int(''.join(filter(str.isdigit, price_str)))
            quantity = int(frame.grid_slaves(row=0, column=2)[0].cget("text"))
            total_price += price * quantity
        except (IndexError, ValueError):
            continue

    total_price_label.config(text=f"총 합: {total_price}원")

    # 총 합을 결제하기 버튼 바로 위, 그리고 메뉴가 추가되는 그리드 아래에 출력
    total_price_label.pack(side='top', pady=(10, 0))  # 상단에 위치하며 아래쪽으로 일정 간격을 두기 위해 pady 추가



# 스크롤이 필요한 경우에만 스크롤을 활성화하도록 함수 수정
def update_scroll():
    # 내부 프레임의 크기 업데이트
    cart_content_frame.update_idletasks()  # 추가된 부분
    # 캔버스의 스크롤 영역을 내부 프레임에 맞게 설정
    canvas.config(scrollregion=canvas.bbox("all"))

    # 현재 내부 프레임의 높이와 캔버스의 높이를 비교하여 스크롤 활성화 여부 결정
    if cart_content_frame.winfo_reqheight() > canvas.winfo_height():
        scrollbar.grid(row=0, column=1, sticky='ns')  # 스크롤바를 오른쪽에 위치시키고 세로로 채우도록 설정
    else:
        scrollbar.grid_forget()  # 스크롤바를 숨김

# 각 열의 너비를 설정
root.columnconfigure(4, weight=0)  # 다섯 번째 열 (비율에 따라 조정)

# 장바구니 프레임에 내용 추가 (예: 텍스트 라벨)
cart_image = PhotoImage(file='./img/shopping_cart.png')

# cart_content_frame의 크기 설정
cart_content_frame = Frame(cart_frame, bg="white", width=500, height=500)
cart_content_frame.pack()

# 폰트 설정
cart_label_font = ('Malgun Gothic', 14, 'bold')
table_num_font = ('Malgun Gothic', 14, 'bold')
payment_button_font = ('Malgun Gothic', 14, 'bold')

cart_label = Label(cart_content_frame, image=cart_image, text="장바구니", fg='black', bg="white", compound='left', padx=20, pady=20, font=cart_label_font)
cart_label.grid(row=0, column=0, pady=(0, 5))  # 상단에 위치하며 아래쪽으로 일정 간격을 두기 위해 pady 추가

# 간격을 추가하기 위한 빈 라벨
spacing_label = Label(cart_content_frame, text="      ", bg="white", padx=5)
spacing_label.grid(row=0, column=1)

table_num = Label(cart_content_frame, text="테이블 2", fg='white', bg="#088A29", padx=10, pady=10, font=table_num_font)
table_num.grid(row=0, column=2, padx=10, pady=10)  # table_num을 우측에 위치시키기 위해 padx 추가

# 결제하기 버튼
payment_button = ttk.Button(cart_frame, text="결제하기", command=save_order_to_csv, style='TButton.Payment.TButton', width=20)
payment_button.pack(side='bottom', fill='x')  # 하단에 위치하며 위쪽으로 일정 간격을 두기 위해 pady 추가

# 메뉴 리스트 프레임 생성
menu_list_frame = Frame(root, bg="#686666")
menu_list_frame.grid(row=1, column=1, sticky='nsew', columnspan=3, rowspan=5)  

# 스크롤바 생성
scrollbar = ttk.Scrollbar(menu_list_frame, orient='vertical', command=Canvas.yview)
scrollbar.grid(row=0, column=1, sticky='ns')  # 스크롤바를 오른쪽에 위치시키고 세로로 채우도록 설정

# 스크롤 가능한 콘텐츠를 위한 캔버스
canvas = Canvas(menu_list_frame, bg="#686666", highlightthickness=0, yscrollcommand=scrollbar.set)
canvas.grid(row=0, column=0, sticky='nsew')

# 캔버스 내부의 내부 프레임
menu_list_inner_frame = Frame(canvas, bg="#686666")

# 메뉴 리스트 프레임 내에서의 위치 조정
menu_list_inner_frame.grid(row=0, column=0)

canvas.create_window((0, 0), window=menu_list_inner_frame, anchor='nw')

# 스크롤바와 Canvas 연결
scrollbar.config(command=canvas.yview)

canvas.bind_all("<MouseWheel>", on_mousewheel)

# 내부 프레임 추천 메뉴 레이블
recommend_label = Label(menu_list_inner_frame, text="추천메뉴", font=('Malgun Gothic', 14, 'bold'), bg='#686666', fg='white')
recommend_label.grid(row=0, column=0)

# 메뉴 1
quantity_var_menu1 = IntVar()
menu1_image = PhotoImage(file='./img/chicken.png')
menu1_btn = Button(menu_list_inner_frame, text="탁탁후라이드치킨\n15000원", image=menu1_image, compound='top', bg='#535050', fg='white', command=lambda:add_to_cart("탁탁후라이드치킨", "15000", quantity_var_menu1))
menu1_btn.grid(row=1, column=0)

# 메뉴 2
quantity_var_menu2 = IntVar()
menu2_image = PhotoImage(file='./img/전.png')
menu2_btn = Button(menu_list_inner_frame, text="탁탁해물파전\n10000원", image=menu2_image, compound='top', bg='#535050', fg='white', command=lambda:add_to_cart("탁탁해물파전", "10000", quantity_var_menu2))
menu2_btn.grid(row=1, column=1)

# 메뉴 3
quantity_var_menu3 = IntVar()
menu3_image = PhotoImage(file='./img/생탁막걸리.png')
menu3_btn = Button(menu_list_inner_frame, text="생탁막걸리\n5000원", image=menu3_image, compound='top', bg='#535050', fg='white', command=lambda:add_to_cart("생탁막걸리", "5000", quantity_var_menu3))
menu3_btn.grid(row=1, column=2)

Label(menu_list_inner_frame, bg='#686666', height=5).grid(row=2, column=0)

# 내부 프레임 메인 메뉴 레이블
main_menu_label = Label(menu_list_inner_frame, text="메인메뉴", font=('Malgun Gothic', 14, 'bold'), bg='#686666', fg='white')
main_menu_label.grid(row=3, column=0)

# 메뉴 1 (메인 메뉴)
menu1_btn = Button(menu_list_inner_frame, text="탁탁후라이드치킨\n15000원", image=menu1_image, compound='top', bg='#535050', fg='white', command=lambda:add_to_cart("탁탁후라이드치킨", "15000", quantity_var_menu1))
menu1_btn.grid(row=4, column=0)

# 메뉴 4
quantity_var_menu4 = IntVar()
menu4_image = PhotoImage(file='./img/곱창전골.png')
menu4_btn = Button(menu_list_inner_frame, text="곱창탁전골\n12000원", image=menu4_image, compound='top', bg='#535050', fg='white', command=lambda:add_to_cart("곱창탁전골", "12000", quantity_var_menu4))
menu4_btn.grid(row=4, column=1)

# 메뉴 5
quantity_var_menu5 = IntVar()
menu5_image = PhotoImage(file='./img/돼지불백.png')
menu5_btn = Button(menu_list_inner_frame, text="돼지탁탁불백\n9000원", image=menu5_image, compound='top', bg='#535050', fg='white', command=lambda:add_to_cart("돼지탁탁불백", "9000", quantity_var_menu5))
menu5_btn.grid(row=4, column=2)

# 메뉴 6
quantity_var_menu6 = IntVar()
menu6_image = PhotoImage(file='./img/골뱅이무침.png')
menu6_btn = Button(menu_list_inner_frame, text="골뱅이탁탁무침\n13000원", image=menu6_image, compound='top', bg='#535050', fg='white', command=lambda:add_to_cart("골뱅이탁탁무침", "13000", quantity_var_menu6))
menu6_btn.grid(row=5, column=0)

# 메뉴 7
quantity_var_menu7 = IntVar()
menu7_image = PhotoImage(file='./img/국물닭발.png')
menu7_btn = Button(menu_list_inner_frame, text="국물탁발\n12500원", image=menu7_image, compound='top', bg='#535050', fg='white', command=lambda:add_to_cart("국물탁발", "12500", quantity_var_menu7))
menu7_btn.grid(row=5, column=1)

# 메뉴 8
quantity_var_menu8 = IntVar()
menu8_image = PhotoImage(file='./img/해장라면.png')
menu8_btn = Button(menu_list_inner_frame, text="해장탁라면\n7000원", image=menu8_image, compound='top', bg='#535050', fg='white', command=lambda:add_to_cart("해장탁라면", "7000", quantity_var_menu8))
menu8_btn.grid(row=5, column=2)

Label(menu_list_inner_frame, bg='#686666', height=5).grid(row=6, column=0)

# 내부 프레임 안주 레이블
an_ju_label = Label(menu_list_inner_frame, text="안주", font=('Malgun Gothic', 14, 'bold'), bg='#686666', fg='white')
an_ju_label.grid(row=7, column=0)

# 메뉴 2 (안주)
menu2_btn = Button(menu_list_inner_frame, text="탁탁해물파전\n10000원", image=menu2_image, compound='top', bg='#535050', fg='white', command=lambda:add_to_cart("탁탁해물파전", "10000", quantity_var_menu2))
menu2_btn.grid(row=8, column=0)

# 메뉴 9
quantity_var_menu9 = IntVar()
menu9_image = PhotoImage(file='./img/반건조오징어.png')
menu9_btn = Button(menu_list_inner_frame, text="반건조탁징어\n5000원", image=menu9_image, compound='top', bg='#535050', fg='white', command=lambda:add_to_cart("반건조탁징어", "5000", quantity_var_menu9))
menu9_btn.grid(row=8, column=1)

# 메뉴 10
quantity_var_menu10 = IntVar()
menu10_image = PhotoImage(file='./img/두부김치.png')
menu10_btn = Button(menu_list_inner_frame, text="두부김치\n11500원", image=menu10_image, compound='top', bg='#535050', fg='white', command=lambda:add_to_cart("두부김치", "11500", quantity_var_menu10))
menu10_btn.grid(row=8, column=2)

Label(menu_list_inner_frame, bg='#686666', height=5).grid(row=9, column=0)

# 내부 프레임 주류 레이블
alco_label = Label(menu_list_inner_frame, text="주류", font=('Malgun Gothic', 14, 'bold'), bg='#686666', fg='white')
alco_label.grid(row=10, column=0)

# 메뉴 3 (주류)
menu3_btn = Button(menu_list_inner_frame, text="생탁막걸리\n5000원", image=menu3_image, compound='top', bg='#535050', fg='white', command=lambda:add_to_cart("생탁막걸리", "5000", quantity_var_menu3))
menu3_btn.grid(row=11, column=0)

# 메뉴 11
quantity_var_menu11 = IntVar()
menu11_image = PhotoImage(file='./img/참이슬.png')
menu11_btn = Button(menu_list_inner_frame, text="참이슬\n5000원", image=menu11_image, compound='top', bg='#535050', fg='white', command=lambda:add_to_cart("참이슬", "5000", quantity_var_menu11))
menu11_btn.grid(row=11, column=1)

# 메뉴 12
quantity_var_menu12 = IntVar()
menu12_image = PhotoImage(file='./img/카스.png')
menu12_btn = Button(menu_list_inner_frame, text="카스\n5000원", image=menu12_image, compound='top', bg='#535050', fg='white', command=lambda:add_to_cart("카스", "5000", quantity_var_menu12))
menu12_btn.grid(row=11, column=2)

# 내부 프레임의 크기를 내부 컨텐츠에 맞게 설정
menu_list_inner_frame.update_idletasks()  # 내부 프레임의 크기 업데이트
canvas.config(scrollregion=canvas.bbox("all"))  # 캔버스의 스크롤 영역을 내부 프레임에 맞게 설정

# menu_list_frame이 cart_frame과 bottom_frame에 닿도록 설정
menu_list_frame.grid_rowconfigure(0, weight=1)  # menu_list_frame의 첫 번째 행을 비율에 따라 조정
menu_list_frame.grid_rowconfigure(1, weight=0)  # menu_list_frame의 두 번째 행은 고정 크기로 설정
menu_list_frame.grid_columnconfigure(0, weight=1)

# 맨 밑에 프레임
bottom_frame = Frame(root, bg="#313131")
bottom_frame.grid(row=6, column=0, columnspan=4, sticky='nsew')  # 메인 로고 프레임과 cart 프레임 전까지 너비가 커져서 출력되도록 설정

# 각각의 버튼 추가
bell_image = PhotoImage(file='./img/bell.png')
call_button = Button(bottom_frame, text="직원호출", command=info, bg='#088A29', fg='white', image=bell_image, compound='left', font=('Malgun Gothic', 14, 'bold'), padx=5)
order_history_button = Button(bottom_frame, text="주문내역", command=show_order_history, bg='white', fg='black', font=('Malgun Gothic', 14, 'bold'), padx=5)
cog_image = PhotoImage(file='./img/cog.png')
settings_button = Button(bottom_frame, text="설정", command=show_setting, bg='white', fg='black', image=cog_image, compound='left', font=('Malgun Gothic', 14, 'bold'), padx=5)

call_button.grid(row=0, column=0, sticky='nsew', pady=5, padx=20)
order_history_button.grid(row=0, column=1, sticky='nsew', pady=5, padx=5)
settings_button.grid(row=0, column=2, sticky='nsew', pady=5, padx=400)



root.mainloop()