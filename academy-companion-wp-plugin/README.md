# Academy Companion WordPress Plugin v2.1

A floating chat widget that provides AI-powered assistance to your Creative Path Academy members.

## Features

✅ **Floating Chat Widget** - Professional chat bubble in corner of website
✅ **Membership Integration** - Only shows to logged-in users with proper roles
✅ **Page Restrictions** - Control which pages show the chat
✅ **Admin Settings** - Easy configuration through WordPress admin
✅ **Mobile Responsive** - Works great on all devices
✅ **Custom Styling** - Beautiful sky blue theme with configurable positioning
✅ **Enhanced Formatting** - Rich text responses with bold headers and bullet lists

## Installation

1. Upload the `academy-companion-wp-plugin` folder to `/wp-content/plugins/`
2. Activate the plugin through WordPress Admin → Plugins
3. Go to Settings → Academy Chat to configure

## Configuration

### Admin Settings (Settings → Academy Chat)

**Enable Chat Widget**: Turn the floating widget on/off

**Allowed User Roles**: Choose which WordPress user roles can see the chat
- **Default: "Academy Member" only** (recommended for paid member access)
- Can add additional roles if needed (Subscriber, Customer, etc.)
- Multiple roles can be selected

**Page Restrictions**:
- **All Pages**: Show chat everywhere
- **Member Pages Only**: Only on pages that require membership
- **Specific Pages**: Manually selected pages (coming soon)

**Bubble Position**: Bottom-right or bottom-left corner

**Bubble Color**: Custom color picker for the chat button

### Membership Integration

The plugin automatically integrates with popular membership plugins:

**Built-in Detection**:
- Pages with `requires_membership` custom field
- Posts with `members-only` category or `academy-content` tag
- Page names containing "member"
- **Default: Restrictive** - only shows on specifically marked member content

**Plugin Integration**:
- **MemberPress**: Uses `mepr_user_has_access()`
- **WooCommerce Memberships**: Uses `wc_memberships_is_post_content_restricted()`

**Custom Integration**: Edit the `academy_companion_is_member_page()` function in `academy-companion.php`

## Usage

### For Site Visitors
1. Log in to your member account
2. Navigate to a member page
3. Click the floating chat bubble (bottom corner)
4. Ask questions about photography, business, techniques
5. Get personalized responses with source citations

### For Administrators
1. Monitor usage through Academy Companion admin dashboard
2. Upload new content through the dashboard
3. Configure chat settings through WordPress admin

## Shortcode Support

You can also embed the chat directly in content using:
```
[academy_chat]
```

This creates an embedded chat interface instead of the floating widget.

## Customization

### Styling
Edit `css/chat.css` to customize the appearance:
- Chat bubble size and animation
- Chat window colors and layout
- Mobile responsive breakpoints

### Functionality
Edit `js/chat.js` to customize behavior:
- Auto-open after delay
- Typing indicators
- Custom welcome messages

### Member Page Detection
Edit the `academy_companion_is_member_page()` function in `academy-companion.php` to customize which pages show the chat.

## API Configuration

The plugin connects to your Academy Companion backend API:
- Default URL: `https://academy-ai-production.up.railway.app`
- Change in `academy-companion.php` line 38 if needed

## Troubleshooting

**Chat not appearing**: Check that user is logged in and has proper role

**"Undefined" responses**: Check that API is working and OpenAI key is valid

**Not showing on member pages**: Customize `academy_companion_is_member_page()` function

**Styling conflicts**: CSS uses `!important` declarations to override theme styles

## Support

For technical support or customization requests, contact your development team.
