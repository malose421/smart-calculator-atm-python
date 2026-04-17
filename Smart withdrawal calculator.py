from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4
import tkinter as tk
from tkinter import messagebox

CurrencyCode = "ZAR"
CurrencyName = "South African Rand"


@dataclass
class CardDetails:
    card_number: str
    expiry_date: str
    cvc: str


@dataclass
class TransactionResult:
    approved: bool
    transaction_id: str
    message: str


def is_valid_card_number(card_number: str) -> bool:
    digits = card_number.replace(" ", "")
    if not digits.isdigit() or not 13 <= len(digits) <= 19:
        return False

    total = 0
    for index, digit in enumerate(digits[::-1]):
        value = int(digit)
        if index % 2 == 1:
            value *= 2
            if value > 9:
                value -= 9
        total += value
    return total % 10 == 0


def is_valid_expiry_date(expiry_date: str) -> bool:
    try:
        expiry = datetime.strptime(expiry_date, "%m/%y")
    except ValueError:
        return False

    current = datetime.now()
    return (expiry.year > current.year) or (
        expiry.year == current.year and expiry.month >= current.month
    )


def is_valid_cvc(cvc: str) -> bool:
    return cvc.isdigit() and len(cvc) in {3, 4}


def calculate_remaining_balance(current_balance: float, withdrawal_amount: float) -> float:
    return current_balance - withdrawal_amount


def calculate_withdrawal_percentage(current_balance: float, withdrawal_amount: float) -> float:
    return (withdrawal_amount / current_balance) * 100


def process_transaction(
    amount: float,
    card_details: CardDetails,
    current_balance: float,
) -> TransactionResult:
    if amount <= 0:
        return TransactionResult(False, "", "Withdrawal amount must be greater than zero.")

    if amount > current_balance:
        return TransactionResult(False, "", "Insufficient funds for this withdrawal.")

    if not is_valid_card_number(card_details.card_number):
        return TransactionResult(False, "", "Card number validation failed.")

    if not is_valid_expiry_date(card_details.expiry_date):
        return TransactionResult(False, "", "Card expiry date is invalid or expired.")

    if not is_valid_cvc(card_details.cvc):
        return TransactionResult(False, "", "CVC validation failed.")

    transaction_id = f"TXN-{uuid4().hex[:12].upper()}"
    return TransactionResult(True, transaction_id, "Transaction approved.")


def build_withdrawal_summary(balance: float, amount: float) -> str:
    if balance <= 0:
        return "Enter a positive account balance to see the withdrawal summary."

    if amount <= 0:
        return "Enter a positive withdrawal amount to see the withdrawal summary."

    if amount > balance:
        return (
            f"Balance: R{balance:.2f}\n"
            f"Withdrawal: R{amount:.2f}\n"
            "Status: Insufficient funds for this withdrawal."
        )

    percentage = calculate_withdrawal_percentage(balance, amount)
    remaining = calculate_remaining_balance(balance, amount)
    return (
        f"Balance: R{balance:.2f}\n"
        f"Withdrawal: R{amount:.2f}\n"
        f"Percentage of balance: {percentage:.2f}%\n"
        f"Projected remaining balance: R{remaining:.2f}"
    )


class CalculatorApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Smart Calculator and ATM")
        self.geometry("960x620")
        self.minsize(860, 560)
        self.configure(bg="#1a1f2b")

        self.calculator_expression = tk.StringVar(value="0")
        self.calculator_history = tk.StringVar(value="Ready")
        self.atm_status = tk.StringVar(value="Insert card details and confirm withdrawal.")
        self.balance_var = tk.StringVar(value="5000")
        self.amount_var = tk.StringVar(value="500")
        self.card_var = tk.StringVar()
        self.expiry_var = tk.StringVar()
        self.cvc_var = tk.StringVar()
        self.summary_var = tk.StringVar(value=self.build_summary(5000.0, 500.0))

        self.create_layout()
        self.bind("<Key>", self.handle_keyboard_input)
        self.update_summary()

    def create_layout(self) -> None:
        container = tk.Frame(self, bg="#1a1f2b")
        container.pack(fill="both", expand=True, padx=18, pady=18)
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)
        container.grid_rowconfigure(0, weight=1)

        calculator_frame = self.create_calculator_frame(container)
        calculator_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        atm_frame = self.create_atm_frame(container)
        atm_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

    def create_calculator_frame(self, parent: tk.Widget) -> tk.Frame:
        frame = tk.Frame(parent, bg="#141924", bd=0, highlightthickness=0)
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        header = tk.Label(
            frame,
            text="Calculator Screen",
            font=("Segoe UI", 22, "bold"),
            bg="#141924",
            fg="#f5f7fb",
            anchor="w",
        )
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 8))

        display_panel = tk.Frame(frame, bg="#0b1020", bd=0)
        display_panel.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 16))
        display_panel.grid_columnconfigure(0, weight=1)

        history_label = tk.Label(
            display_panel,
            textvariable=self.calculator_history,
            font=("Consolas", 12),
            bg="#0b1020",
            fg="#7d8aa6",
            anchor="e",
        )
        history_label.grid(row=0, column=0, sticky="ew", padx=18, pady=(18, 6))

        output_label = tk.Label(
            display_panel,
            textvariable=self.calculator_expression,
            font=("Consolas", 30, "bold"),
            bg="#0b1020",
            fg="#f8fbff",
            anchor="e",
        )
        output_label.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 18))

        button_panel = tk.Frame(frame, bg="#141924")
        button_panel.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))
        for column in range(4):
            button_panel.grid_columnconfigure(column, weight=1)
        for row in range(5):
            button_panel.grid_rowconfigure(row, weight=1)

        buttons = [
            ("C", 0, 0, "#e85d75", self.clear_calculator),
            ("DEL", 0, 1, "#f09a45", self.delete_last),
            ("%", 0, 2, "#3f6fd1", lambda: self.append_to_expression("%")),
            ("/", 0, 3, "#3f6fd1", lambda: self.append_to_expression("/")),
            ("7", 1, 0, "#21283b", lambda: self.append_to_expression("7")),
            ("8", 1, 1, "#21283b", lambda: self.append_to_expression("8")),
            ("9", 1, 2, "#21283b", lambda: self.append_to_expression("9")),
            ("*", 1, 3, "#3f6fd1", lambda: self.append_to_expression("*")),
            ("4", 2, 0, "#21283b", lambda: self.append_to_expression("4")),
            ("5", 2, 1, "#21283b", lambda: self.append_to_expression("5")),
            ("6", 2, 2, "#21283b", lambda: self.append_to_expression("6")),
            ("-", 2, 3, "#3f6fd1", lambda: self.append_to_expression("-")),
            ("1", 3, 0, "#21283b", lambda: self.append_to_expression("1")),
            ("2", 3, 1, "#21283b", lambda: self.append_to_expression("2")),
            ("3", 3, 2, "#21283b", lambda: self.append_to_expression("3")),
            ("+", 3, 3, "#3f6fd1", lambda: self.append_to_expression("+")),
            ("0", 4, 0, "#21283b", lambda: self.append_to_expression("0")),
            (".", 4, 1, "#21283b", lambda: self.append_to_expression(".")),
            ("(", 4, 2, "#21283b", lambda: self.append_to_expression("(")),
            (")", 4, 3, "#21283b", lambda: self.append_to_expression(")")),
        ]

        for text, row, column, color, command in buttons:
            button = tk.Button(
                button_panel,
                text=text,
                command=command,
                font=("Segoe UI", 17, "bold"),
                bg=color,
                fg="#ffffff",
                activebackground=color,
                activeforeground="#ffffff",
                relief="flat",
                bd=0,
                cursor="hand2",
            )
            button.grid(row=row, column=column, sticky="nsew", padx=6, pady=6)

        equals_button = tk.Button(
            frame,
            text="=",
            command=self.evaluate_expression,
            font=("Segoe UI", 20, "bold"),
            bg="#19a974",
            fg="#ffffff",
            activebackground="#19a974",
            activeforeground="#ffffff",
            relief="flat",
            bd=0,
            cursor="hand2",
            height=2,
        )
        equals_button.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 20))
        return frame

    def create_atm_frame(self, parent: tk.Widget) -> tk.Frame:
        frame = tk.Frame(parent, bg="#0d3b2a", bd=0)
        frame.grid_columnconfigure(0, weight=1)

        top_panel = tk.Frame(frame, bg="#144d38")
        top_panel.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 14))
        top_panel.grid_columnconfigure(0, weight=1)

        title = tk.Label(
            top_panel,
            text="ATM Withdrawal Screen",
            font=("Segoe UI", 22, "bold"),
            bg="#144d38",
            fg="#effff7",
            anchor="w",
        )
        title.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 2))

        subtitle = tk.Label(
            top_panel,
            text=f"Currency: {CurrencyCode} ({CurrencyName})",
            font=("Segoe UI", 11),
            bg="#144d38",
            fg="#b9ecd3",
            anchor="w",
        )
        subtitle.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 14))

        screen = tk.Frame(frame, bg="#c8f2dd", bd=0, highlightbackground="#7dd4aa", highlightthickness=3)
        screen.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 14))
        screen.grid_columnconfigure(0, weight=1)
        screen.grid_columnconfigure(1, weight=1)

        screen_title = tk.Label(
            screen,
            text="Cash Withdrawal",
            font=("Consolas", 20, "bold"),
            bg="#c8f2dd",
            fg="#103e2d",
        )
        screen_title.grid(row=0, column=0, columnspan=2, sticky="ew", padx=18, pady=(16, 6))

        status = tk.Label(
            screen,
            textvariable=self.atm_status,
            font=("Consolas", 11),
            bg="#c8f2dd",
            fg="#1d5a42",
            justify="left",
            wraplength=360,
        )
        status.grid(row=1, column=0, columnspan=2, sticky="ew", padx=18, pady=(0, 12))

        labels = [
            ("Account Balance", self.balance_var),
            ("Withdrawal Amount", self.amount_var),
            ("Card Number", self.card_var),
            ("Expiry Date", self.expiry_var),
            ("CVC", self.cvc_var),
        ]

        for index, (label_text, variable) in enumerate(labels, start=2):
            label = tk.Label(
                screen,
                text=label_text,
                font=("Segoe UI", 11, "bold"),
                bg="#c8f2dd",
                fg="#103e2d",
                anchor="w",
            )
            label.grid(row=index, column=0, sticky="ew", padx=(18, 10), pady=6)

            show = "*" if label_text == "CVC" else ""
            entry = tk.Entry(
                screen,
                textvariable=variable,
                font=("Consolas", 13),
                bg="#f7fffb",
                fg="#103e2d",
                insertbackground="#103e2d",
                relief="flat",
                show=show,
            )
            entry.grid(row=index, column=1, sticky="ew", padx=(10, 18), pady=6, ipadx=8, ipady=8)
            if variable in (self.balance_var, self.amount_var, self.card_var, self.expiry_var):
                variable.trace_add("write", self.update_summary)

        self.cvc_var.trace_add("write", self.update_summary)

        summary_label = tk.Label(
            screen,
            textvariable=self.summary_var,
            font=("Consolas", 11),
            bg="#b5ead0",
            fg="#103e2d",
            justify="left",
            anchor="w",
            padx=12,
            pady=10,
        )
        summary_label.grid(row=7, column=0, columnspan=2, sticky="ew", padx=18, pady=(14, 18))

        side_controls = tk.Frame(frame, bg="#0d3b2a")
        side_controls.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))
        for column in range(2):
            side_controls.grid_columnconfigure(column, weight=1)

        quick_amounts = [200, 500, 1000, 2000]
        for index, amount in enumerate(quick_amounts):
            button = tk.Button(
                side_controls,
                text=f"Quick R{amount}",
                command=lambda value=amount: self.set_quick_amount(value),
                font=("Segoe UI", 11, "bold"),
                bg="#1d6b4d",
                fg="#ffffff",
                activebackground="#1d6b4d",
                activeforeground="#ffffff",
                relief="flat",
                bd=0,
                cursor="hand2",
            )
            button.grid(row=index // 2, column=index % 2, sticky="ew", padx=6, pady=6, ipady=10)

        action_panel = tk.Frame(frame, bg="#0d3b2a")
        action_panel.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 20))
        for column in range(2):
            action_panel.grid_columnconfigure(column, weight=1)

        clear_button = tk.Button(
            action_panel,
            text="Clear",
            command=self.clear_atm_fields,
            font=("Segoe UI", 12, "bold"),
            bg="#7f8c8d",
            fg="#ffffff",
            activebackground="#7f8c8d",
            activeforeground="#ffffff",
            relief="flat",
            bd=0,
            cursor="hand2",
        )
        clear_button.grid(row=0, column=0, sticky="ew", padx=(0, 6), ipady=12)

        confirm_button = tk.Button(
            action_panel,
            text="Confirm Withdrawal",
            command=self.handle_withdrawal,
            font=("Segoe UI", 12, "bold"),
            bg="#f4b400",
            fg="#102119",
            activebackground="#f4b400",
            activeforeground="#102119",
            relief="flat",
            bd=0,
            cursor="hand2",
        )
        confirm_button.grid(row=0, column=1, sticky="ew", padx=(6, 0), ipady=12)
        return frame

    def append_to_expression(self, value: str) -> None:
        current = self.calculator_expression.get()
        if current == "0":
            current = ""
        self.calculator_expression.set(current + value)

    def clear_calculator(self) -> None:
        self.calculator_expression.set("0")
        self.calculator_history.set("Ready")

    def delete_last(self) -> None:
        current = self.calculator_expression.get()
        if len(current) <= 1:
            self.calculator_expression.set("0")
            return
        self.calculator_expression.set(current[:-1])

    def evaluate_expression(self) -> None:
        expression = self.calculator_expression.get().replace("%", "/100")
        try:
            result = eval(expression, {"__builtins__": {}}, {})
        except Exception:
            self.calculator_history.set("Invalid expression")
            return

        self.calculator_history.set(self.calculator_expression.get())
        self.calculator_expression.set(str(result))

    def handle_keyboard_input(self, event: tk.Event) -> None:
        if self.focus_get() and isinstance(self.focus_get(), tk.Entry):
            return

        if event.char in "0123456789+-*/().%":
            self.append_to_expression(event.char)
        elif event.keysym == "Return":
            self.evaluate_expression()
        elif event.keysym == "BackSpace":
            self.delete_last()
        elif event.keysym == "Escape":
            self.clear_calculator()

    def set_quick_amount(self, amount: int) -> None:
        self.amount_var.set(str(amount))
        self.atm_status.set(f"Quick withdrawal amount selected: R{amount:.2f}")

    def clear_atm_fields(self) -> None:
        self.balance_var.set("5000")
        self.amount_var.set("500")
        self.card_var.set("")
        self.expiry_var.set("")
        self.cvc_var.set("")
        self.atm_status.set("Insert card details and confirm withdrawal.")
        self.update_summary()

    def parse_positive_amount(self, raw_value: str, label: str) -> float:
        try:
            amount = float(raw_value)
        except ValueError as error:
            raise ValueError(f"{label} must be a valid number.") from error

        if amount <= 0:
            raise ValueError(f"{label} must be greater than zero.")
        return amount

    def build_summary(self, balance: float, amount: float) -> str:
        return build_withdrawal_summary(balance, amount)

    def update_summary(self, *args: object) -> None:
        try:
            balance = float(self.balance_var.get())
            amount = float(self.amount_var.get())
        except ValueError:
            self.summary_var.set("Enter numeric values for balance and withdrawal amount.")
            return

        self.summary_var.set(self.build_summary(balance, amount))

    def handle_withdrawal(self) -> None:
        try:
            current_balance = self.parse_positive_amount(self.balance_var.get(), "Account balance")
            withdrawal_amount = self.parse_positive_amount(self.amount_var.get(), "Withdrawal amount")
        except ValueError as error:
            self.atm_status.set(str(error))
            messagebox.showerror("Withdrawal Error", str(error))
            return

        card_details = CardDetails(
            card_number=self.card_var.get().strip(),
            expiry_date=self.expiry_var.get().strip(),
            cvc=self.cvc_var.get().strip(),
        )

        if not messagebox.askyesno(
            "Confirm Withdrawal",
            f"Withdraw R{withdrawal_amount:.2f} from your account?",
        ):
            self.atm_status.set("Withdrawal cancelled before processing.")
            return

        transaction = process_transaction(
            amount=withdrawal_amount,
            card_details=card_details,
            current_balance=current_balance,
        )

        if not transaction.approved:
            self.atm_status.set(transaction.message)
            messagebox.showerror("Transaction Failed", transaction.message)
            return

        remaining_balance = calculate_remaining_balance(current_balance, withdrawal_amount)
        percentage = calculate_withdrawal_percentage(current_balance, withdrawal_amount)
        success_message = (
            f"Withdrawal approved.\n"
            f"Amount withdrawn: R{withdrawal_amount:.2f}\n"
            f"Percentage of balance: {percentage:.2f}%\n"
            f"Remaining balance: R{remaining_balance:.2f}\n"
            f"Transaction ID: {transaction.transaction_id}"
        )
        self.balance_var.set(f"{remaining_balance:.2f}")
        self.amount_var.set("0")
        self.atm_status.set(success_message)
        messagebox.showinfo("Transaction Approved", success_message)


if __name__ == "__main__":
    app = CalculatorApp()
    app.mainloop()
