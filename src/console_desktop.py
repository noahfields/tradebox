from textual.app import App, ComposeResult
from textual.containers import HorizontalGroup
from textual.widgets import DataTable, TabbedContent, TabPane, Button, Footer, Header, Label

class RunnerStatus(HorizontalGroup):
    def compose(self) -> ComposeResult:
        yield Label("Positions")
        yield Label(" ", id="runner_active_position")
        yield Label(" ", id="runner_status_position")

        yield Label("Position Market")
        yield Label(" ", id="runner_active_position_mkt_data")
        yield Label(" ", id="runner_status_position_mkt_data")

        yield Label("Broker Orders")
        yield Label(" ", id="runner_active_broker_order")
        yield Label(" ", id="runner_status_broker_order")

        yield Label("Broker Orders Market")
        yield Label(" ", id="runner_active_broker_order_mkt_data")
        yield Label(" ", id="runner_status_broker_order_mkt_data")

        yield Label("Trigger Market")
        yield Label(" ", id="runner_active_trigger_mkt_data")
        yield Label(" ", id="runner_status_trigger_mkt_data")

        yield Label("Trailing Orders")
        yield Label(" ", id="runner_active_trailing_orders")
        yield Label(" ", id="runner_status_trailing_orders")
        
        yield Label("Trailing Market")
        yield Label(" ", id="runner_active_trailing_orders_mkt_data")
        yield Label(" ", id="runner_status_trailing_orders_mkt_data")

        yield Label("Bracket Orders")
        yield Label(" ", id="runner_active_bracket_orders")
        yield Label(" ", id="runner_status_bracket_orders")
        
        yield Label("Trailing Market")
        yield Label(" ", id="runner_active_trailing_orders_")
        yield Label(" ", id="runner_status_trailing_orders")


class RobinhoodManagementButtons(HorizontalGroup):
    def compose(self) -> ComposeResult:
        yield Button("Login", variant="success")
        yield Button("Logout", variant="error")


class TradeboxDesktop(App):
    """A Textual app for tradebox."""

    CSS_PATH = "console_desktop.tcss"
    BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent():
            with TabPane("Main"):
                runner_status = RunnerStatus()
                yield runner_status
            with TabPane("System Management"):
                robinhood_management_buttons = RobinhoodManagementButtons()
                yield robinhood_management_buttons
        yield Footer()


    # def create_position_datatable(self):
    #     positions_table = DataTable(id="positions")
    #     positions_table.add_columns("Symbol", "Quantity", "Entry Price", "Current Price", "P&L")
    #     positions_table.add_row("AAPL", "100", "$150.00", "$155.50", "+$550.00")
    #     return positions_table
        
        # orders_table = DataTable(id="orders")
        # orders_table.add_columns("Order ID", "Symbol", "Type", "Quantity", "Price", "Status")
        # orders_table.add_row("ORD001", "TSLA", "BUY", "25", "$245.00", "FILLED")

        # trigger_orders_table = DataTable(id="trigger_orders")
        # trigger_orders_table.add_columns("Order ID", "Symbol", "Type", "Quantity", "Price", "Status")
        # trigger_orders_table.add_row("ORD001", "TSLA", "BUY", "25", "$245.00", "FILLED")

        # trailing_orders_table = DataTable(id="trailing_orders")
        # trailing_orders_table.add_columns("Order ID", "Symbol", "Type", "Quantity", "Price", "Status")
        # trailing_orders_table.add_row("ORD001", "TSLA", "BUY", "25", "$245.00", "FILLED")

        # bracket_orders_table = DataTable(id="bracket_orders")
        # bracket_orders_table.add_columns("Order ID", "Symbol", "Type", "Quantity", "Price", "Status")
        # bracket_orders_table.add_row("ORD001", "TSLA", "BUY", "25", "$245.00", "FILLED")
        
        # return [positions_table, orders_table, trigger_orders_table, trailing_orders_table, bracket_orders_table]

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )


if __name__ == "__main__":
    app = TradeboxDesktop()
    app.run()