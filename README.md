# Twilio Demo Website - Electronics Store

A fully functional e-commerce demo showcasing Twilio Flex WebChat and Segment Analytics integration. This single-page application demonstrates how to track customer behavior and provide live chat support in an online electronics store.

## Features

### E-commerce Functionality
- Product catalog with detailed product views
- Shopping cart with persistence (localStorage)
- User authentication (login/signup)
- Checkout flow with order completion
- Responsive design

### Segment Analytics Integration
Tracks the following events according to Segment's E-commerce Spec:
- **Page Views** - Navigation between products, cart, and checkout
- **Product Clicked** - User clicks on a product
- **Product Viewed** - Product detail modal opens
- **Product Added** - Item added to cart
- **Product Removed** - Item removed from cart
- **Checkout Started** - User enters checkout flow
- **Order Completed** - Order successfully placed
- **Identify** - User login/signup with profile data
- **Reset** - User logout

### Twilio Flex WebChat Integration
- Pre-engagement form with customizable fields
- Auto-populated email for logged-in users
- Live chat support widget
- Seamless integration with Flex backend

## Setup Instructions

### Prerequisites
- A web server or local development server (e.g., `python -m http.server`, `npx serve`, etc.)
- A Segment account with a write key
- A Twilio Flex account with WebChat configured

### 1. Clone or Download
```bash
git clone <repository-url>
cd twilio-demo-website
```

### 2. Configure Segment Analytics

1. Sign up for [Segment](https://segment.com/) if you don't have an account
2. Create a new Source (JavaScript)
3. Copy your Write Key
4. Open `index.html` and replace the write key on line 672:
   ```javascript
   analytics.load("YOUR_WRITE_KEY_HERE");
   ```

### 3. Configure Twilio Flex WebChat

1. Set up Twilio Flex and configure WebChat in your Twilio Console
2. Obtain your Deployment Key
3. Open `index.html` and replace the deployment key on line 1620:
   ```javascript
   deploymentKey: "YOUR_DEPLOYMENT_KEY_HERE",
   ```

### 4. Run the Application

Start a local web server:

```bash
# Option 1: Python
python -m http.server 8000

# Option 2: Node.js
npx serve

# Option 3: PHP
php -S localhost:8000
```

Open your browser and navigate to `http://localhost:8000`

## Usage

### Shopping Flow

1. **Browse Products** - View the product catalog on the home page
2. **View Product Details** - Click on any product to see detailed information
3. **Add to Cart** - Select quantity and add items to your shopping cart
4. **Login/Signup** - Create an account or log in with your credentials
5. **Checkout** - Review your order and complete the purchase
6. **Live Chat** - Click the chat widget for customer support

### Testing Segment Events

1. Open your browser's Developer Console (F12)
2. Open the [Segment Debugger](https://app.segment.com/goto-my-workspace/sources/debugger)
3. Perform actions in the app (browse, add to cart, checkout)
4. Watch events appear in real-time in both places

### User Signup Fields

When creating a new account, the following information is captured and sent to Segment:
- User ID
- Email
- First Name
- Last Name
- Birthday
- Phone Number
- Subscription Tier (free, basic, premium, enterprise)
- Created At (timestamp)
- Origin (Website)

## Product Catalog

The demo includes 6 sample products:
- iPhone 15 Pro ($999)
- MacBook Air M2 ($1,199)
- AirPods Pro ($249)
- Sony WH-1000XM5 ($399)
- Samsung Galaxy S24 ($899)
- Dell XPS 15 ($1,499)

## Technical Details

### Architecture
- **Frontend**: Vanilla JavaScript (no frameworks)
- **Styling**: Custom CSS with responsive design
- **Analytics**: Segment Analytics.js
- **Chat**: Twilio Flex WebChat SDK v3.3.0
- **Storage**: localStorage for cart persistence
- **Session**: Segment user traits for session restoration

### State Management
Application state is stored in `window.state`:
```javascript
{
  cart: {},           // { productId: quantity }
  currentUser: null,  // { userId, email }
  currentView: 'products',
  orderCompleted: false
}
```

### Segment Event Properties

All e-commerce events follow [Segment's E-commerce Spec v2](https://segment.com/docs/connections/spec/ecommerce/v2/):
- Product events include: product_id, name, brand, category, price, currency
- Order events include: order_id, total, revenue, shipping, tax, products array
- Cart events include: cart_id, product details, quantity

### Browser Compatibility
- Modern browsers (Chrome, Firefox, Safari, Edge)
- ES6+ JavaScript features
- CSS Grid and Flexbox

## File Structure

```
twilio-demo-website/
├── index.html          # Main application file (HTML + CSS + JS)
└── README.md          # This file
```

## Customization

### Modify Products
Edit the `products` array in index.html (starting at line 699) to add/remove/modify products.

### Customize Styling
All CSS is embedded in the `<style>` section of index.html (lines 8-434).

### Adjust Segment Events
Event tracking functions are located in the "SEGMENT EVENT TRACKING FUNCTIONS" section (lines 824-1001).

### Configure WebChat Appearance
Modify the `appConfig` object in the Twilio initialization script (lines 1619-1659).

## Development Notes

- Cart data persists across page refreshes using localStorage
- User session is restored from Segment Analytics on page load
- All monetary values are in USD
- Tax is calculated at 8% and shipping is a flat $10
- Order IDs are generated using timestamps

## Support

For issues related to:
- **Segment**: Visit [Segment Documentation](https://segment.com/docs/)
- **Twilio Flex**: Visit [Twilio Flex Documentation](https://www.twilio.com/docs/flex)
- **This Demo**: Open an issue in this repository

## License

This is a demo application for educational and demonstration purposes.
