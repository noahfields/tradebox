import sqlite3
from datetime import datetime
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Header, Footer, DataTable, Button, Label, Input, Static
from textual.screen import ModalScreen
from textual.binding import Binding

class SellDialog(ModalScreen):
    """Modal dialog for selling an option position."""
    
    CSS = """
    SellDialog {
        align: center middle;
    }
    
    #dialog {
        width: 60;
        height: 20;
        border: thick $background 80%;
        background: $surface;
        padding: 1 2;
    }
    
    #title {
        width: 100%;
        content-align: center middle;
        text-style: bold;
        margin-bottom: 1;
    }
    
    .detail-row {
        margin: 0 0 0 2;
    }
    
    #quantity-input {
        width: 15;
    }
    
    #button-row {
        width: 100%;
        height: auto;
        align: center middle;
        margin-top: 1;
    }
    """
    
    def __init__(self, position_data, db_name):
        super().__init__()
        self.position_data = position_data
        self.db_name = db_name
    
    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("Sell Option Position", id="title")
            yield Label(f"Symbol: {self.position_data['symbol']}", classes="detail-row")
            yield Label(f"Type: {self.position_data['type']}", classes="detail-row")
            yield Label(f"Strike: ${self.position_data['strike']:.2f}", classes="detail-row")
            yield Label(f"Expiry: {self.position_data['expiry']}", classes="detail-row")
            yield Label(f"Available Quantity: {self.position_data['qty']}", classes="detail-row")
            
            with Horizontal():
                yield Label("Quantity to Sell: ")
                yield Input(
                    value=str(self.position_data['qty']),
                    placeholder="Enter quantity",
                    id="quantity-input"
                )
            
            with Horizontal(id="button-row"):
                yield Button("Confirm Sell", variant="primary", id="confirm")
                yield Button("Cancel", variant="default", id="cancel")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.dismiss(None)
        elif event.button.id == "confirm":
            qty_input = self.query_one("#quantity-input", Input)
            try:
                sell_qty = int(qty_input.value)
                if sell_qty <= 0 or sell_qty > self.position_data['qty']:
                    self.notify(
                        f"Invalid quantity. Must be between 1 and {self.position_data['qty']}",
                        severity="error",
                        timeout=3
                    )
                    return
                
                # Update database
                conn = sqlite3.connect(self.db_name)
                c = conn.cursor()
                
                if sell_qty == self.position_data['qty']:
                    c.execute("DELETE FROM positions WHERE id = ?", 
                             (self.position_data['id'],))
                else:
                    c.execute("UPDATE positions SET quantity = quantity - ? WHERE id = ?",
                             (sell_qty, self.position_data['id']))
                
                conn.commit()
                conn.close()
                
                self.dismiss({
                    'success': True,
                    'quantity': sell_qty,
                    'symbol': self.position_data['symbol']
                })
                
            except ValueError:
                self.notify("Please enter a valid number", severity="error", timeout=3)

class OptionPositionApp(App):
    """Stock Option Position Tracker using Textual."""
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    #title {
        width: 100%;
        content-align: center middle;
        text-style: bold;
        height: 3;
        background: $boost;
    }
    
    #table-container {
        width: 100%;
        height: 1fr;
        border: solid $primary;
        margin: 1 2;
    }
    
    #button-bar {
        width: 100%;
        height: auto;
        align: center middle;
        margin: 1;
    }
    
    #status-bar {
        width: 100%;
        height: 1;
        background: $panel;
        padding: 0 2;
    }
    
    Button {
        margin: 0 1;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("s", "sell", "Sell Selected"),
    ]
    
    def __init__(self):
        super().__init__()
        self.db_name = "options.db"
        self.refresh_interval = 5  # seconds
        self.init_database()
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Label("Stock Option Position Tracker", id="title")
        
        with Container(id="table-container"):
            yield DataTable(id="positions-table")
        
        with Horizontal(id="button-bar"):
            yield Button("Sell Selected", variant="primary", id="sell-btn")
            yield Button("Refresh Now", variant="default", id="refresh-btn")
        
        yield Static("Ready", id="status-bar")
        yield Footer()
    
    def init_database(self):
        """Initialize database with sample data if empty."""
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        
        c.execute('''CREATE TABLE IF NOT EXISTS positions
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      symbol TEXT NOT NULL,
                      option_type TEXT NOT NULL,
                      strike REAL NOT NULL,
                      expiry DATE NOT NULL,
                      quantity INTEGER NOT NULL,
                      avg_price REAL NOT NULL,
                      current_price REAL NOT NULL,
                      updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
        c.execute("SELECT COUNT(*) FROM positions")
        if c.fetchone()[0] == 0:
            sample_data = [
                ('AAPL', 'CALL', 150.0, '2024-03-15', 10, 5.50, 6.20),
                ('GOOGL', 'PUT', 140.0, '2024-04-20', 5, 8.30, 7.90),
                ('MSFT', 'CALL', 380.0, '2024-03-22', 15, 12.40, 13.10),
                ('TSLA', 'CALL', 200.0, '2024-05-17', 8, 18.50, 21.30),
                ('AMZN', 'PUT', 170.0, '2024-06-21', 12, 9.75, 8.90),
            ]
            c.executemany('''INSERT INTO positions 
                           (symbol, option_type, strike, expiry, quantity, avg_price, current_price)
                           VALUES (?, ?, ?, ?, ?, ?, ?)''', sample_data)
            conn.commit()
        
        conn.close()
    
    def on_mount(self) -> None:
        """Set up the data table and start auto-refresh."""
        table = self.query_one("#positions-table", DataTable)
        table.cursor_type = "row"
        table.zebra_stripes = True
        
        # Add columns
        table.add_column("ID", key="id", width=6)
        table.add_column("Symbol", key="symbol", width=8)
        table.add_column("Type", key="type", width=6)
        table.add_column("Strike", key="strike", width=10)
        table.add_column("Expiry", key="expiry", width=12)
        table.add_column("Qty", key="qty", width=6)
        table.add_column("Avg Price", key="avg_price", width=12)
        table.add_column("Current", key="current", width=12)
        table.add_column("P/L", key="pl", width=12)
        table.add_column("P/L %", key="pl_pct", width=10)
        
        # Load initial data
        self.refresh_data()
        
        # Start auto-refresh
        self.set_interval(self.refresh_interval, self.refresh_data)
    
    def refresh_data(self) -> None:
        """Refresh data from database."""
        table = self.query_one("#positions-table", DataTable)
        table.clear()
        
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute("SELECT * FROM positions ORDER BY id")
        rows = c.fetchall()
        conn.close()
        
        for row in rows:
            id, symbol, opt_type, strike, expiry, qty, avg_price, curr_price, _ = row
            
            pl = (curr_price - avg_price) * qty * 100
            pl_pct = ((curr_price - avg_price) / avg_price) * 100
            
            # Format with color coding
            pl_str = f"${pl:,.2f}"
            pl_pct_str = f"{pl_pct:.2f}%"
            
            # Style based on profit/loss
            if pl >= 0:
                pl_str = f"[green]{pl_str}[/green]"
                pl_pct_str = f"[green]{pl_pct_str}[/green]"
            else:
                pl_str = f"[red]{pl_str}[/red]"
                pl_pct_str = f"[red]{pl_pct_str}[/red]"
            
            table.add_row(
                str(id),
                symbol,
                opt_type,
                f"${strike:.2f}",
                expiry,
                str(qty),
                f"${avg_price:.2f}",
                f"${curr_price:.2f}",
                pl_str,
                pl_pct_str,
                key=str(id)
            )
        
        # Update status bar
        now = datetime.now().strftime("%H:%M:%S")
        status = self.query_one("#status-bar", Static)
        status.update(f"Last updated: {now} | Positions: {len(rows)}")
    
    def action_refresh(self) -> None:
        """Manual refresh action."""
        self.refresh_data()
        self.notify("Data refreshed", timeout=2)
    
    def action_sell(self) -> None:
        """Open sell dialog for selected position."""
        self.sell_selected()
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        if event.button.id == "sell-btn":
            self.sell_selected()
        elif event.button.id == "refresh-btn":
            self.action_refresh()
    
    def sell_selected(self) -> None:
        """Open sell dialog for the selected position."""
        table = self.query_one("#positions-table", DataTable)
        
        if table.cursor_row is None or table.cursor_row >= table.row_count:
            self.notify("Please select a position to sell", severity="warning", timeout=3)
            return
        
        # Get selected row data
        row_key = table.get_row_at(table.cursor_row)
        position_id = int(row_key[0])
        
        # Fetch full data from database
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute("SELECT * FROM positions WHERE id = ?", (position_id,))
        row = c.fetchone()
        conn.close()
        
        if not row:
            self.notify("Position not found", severity="error", timeout=3)
            return
        
        position_data = {
            'id': row[0],
            'symbol': row[1],
            'type': row[2],
            'strike': row[3],
            'expiry': row[4],
            'qty': row[5],
            'avg_price': row[6],
            'current_price': row[7]
        }
        
        # Show sell dialog
        self.push_screen(SellDialog(position_data, self.db_name), self.handle_sell_result)
    
    def handle_sell_result(self, result) -> None:
        """Handle the result from the sell dialog."""
        if result and result.get('success'):
            self.notify(
                f"Successfully sold {result['quantity']} contracts of {result['symbol']}",
                severity="information",
                timeout=3
            )
            self.refresh_data()

if __name__ == "__main__":
    app = OptionPositionApp()
    app.run()