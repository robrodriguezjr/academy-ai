<?php
/**
 * Plugin Name: Academy Companion Chat
 * Description: AI chat assistant for Creative Path Academy members with floating widget
 * Version: 2.8
 * Author: Robert Rodriguez Jr
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

// Plugin activation hook
register_activation_hook(__FILE__, 'academy_companion_activate');
function academy_companion_activate() {
    // Set default options
    add_option('academy_companion_enabled', '1');
    add_option('academy_companion_allowed_roles', array('academy_member'));
    add_option('academy_companion_page_restrictions', 'member_pages');
    add_option('academy_companion_bubble_position', 'bottom-right');
    add_option('academy_companion_bubble_color', '#667eea');
}

// Add admin menu
add_action('admin_menu', 'academy_companion_admin_menu');
function academy_companion_admin_menu() {
    add_options_page(
        'Academy Companion Settings',
        'Academy Chat',
        'manage_options',
        'academy-companion',
        'academy_companion_admin_page'
    );
}

// Admin settings page
function academy_companion_admin_page() {
    if (isset($_POST['submit'])) {
        update_option('academy_companion_enabled', isset($_POST['enabled']) ? '1' : '0');
        update_option('academy_companion_allowed_roles', $_POST['allowed_roles'] ?? array());
        update_option('academy_companion_page_restrictions', $_POST['page_restrictions'] ?? 'all');
        update_option('academy_companion_bubble_position', $_POST['bubble_position'] ?? 'bottom-right');
        update_option('academy_companion_bubble_color', $_POST['bubble_color'] ?? '#667eea');
        echo '<div class="notice notice-success"><p>Settings saved!</p></div>';
    }
    
    $enabled = get_option('academy_companion_enabled', '1');
    $allowed_roles = get_option('academy_companion_allowed_roles', array('academy_member'));
    $page_restrictions = get_option('academy_companion_page_restrictions', 'member_pages');
    $bubble_position = get_option('academy_companion_bubble_position', 'bottom-right');
    $bubble_color = get_option('academy_companion_bubble_color', '#667eea');
    
    ?>
    <div class="wrap">
        <h1>Academy Companion Settings</h1>
        <form method="post" action="">
            <table class="form-table">
                <tr>
                    <th scope="row">Enable Chat Widget</th>
                    <td>
                        <input type="checkbox" name="enabled" value="1" <?php checked($enabled, '1'); ?> />
                        <label>Show floating chat widget</label>
                    </td>
                </tr>
                <tr>
                    <th scope="row">Allowed User Roles</th>
                    <td>
                        <?php 
                        $roles = wp_roles()->get_names();
                        foreach ($roles as $role_value => $role_name) : ?>
                            <label>
                                <input type="checkbox" name="allowed_roles[]" value="<?php echo esc_attr($role_value); ?>" 
                                       <?php checked(in_array($role_value, $allowed_roles)); ?> />
                                <?php echo esc_html($role_name); ?>
                            </label><br>
                        <?php endforeach; ?>
                        <p class="description">Select which user roles can see the chat widget<br><strong>Recommended:</strong> Only select "Academy Member" for paid member access</p>
                    </td>
                </tr>
                <tr>
                    <th scope="row">Page Restrictions</th>
                    <td>
                        <select name="page_restrictions">
                            <option value="all" <?php selected($page_restrictions, 'all'); ?>>All Pages</option>
                            <option value="member_pages" <?php selected($page_restrictions, 'member_pages'); ?>>Member Pages Only</option>
                            <option value="specific_pages" <?php selected($page_restrictions, 'specific_pages'); ?>>Specific Pages</option>
                        </select>
                        <p class="description">Control where the chat widget appears</p>
                    </td>
                </tr>
                <tr>
                    <th scope="row">Bubble Position</th>
                    <td>
                        <select name="bubble_position">
                            <option value="bottom-right" <?php selected($bubble_position, 'bottom-right'); ?>>Bottom Right</option>
                            <option value="bottom-left" <?php selected($bubble_position, 'bottom-left'); ?>>Bottom Left</option>
                        </select>
                    </td>
                </tr>
                <tr>
                    <th scope="row">Bubble Color</th>
                    <td>
                        <input type="color" name="bubble_color" value="<?php echo esc_attr($bubble_color); ?>" />
                    </td>
                </tr>
            </table>
            <?php submit_button(); ?>
        </form>
    </div>
    <?php
}

// Check if user should see chat
function academy_companion_user_can_chat() {
    if (!is_user_logged_in()) {
        return false;
    }
    
    $user = wp_get_current_user();
    $allowed_roles = get_option('academy_companion_allowed_roles', array('academy_member'));
    
    // Check if user has any of the allowed roles
    foreach ($allowed_roles as $role) {
        if (in_array($role, $user->roles)) {
            return true;
        }
    }
    
    return false;
}

// Check if chat should show on current page
function academy_companion_should_show_chat() {
    if (!academy_companion_user_can_chat()) {
        return false;
    }
    
    $enabled = get_option('academy_companion_enabled', '1');
    if ($enabled !== '1') {
        return false;
    }
    
    $page_restrictions = get_option('academy_companion_page_restrictions', 'member_pages');
    
    switch ($page_restrictions) {
        case 'all':
            return true;
            
        case 'member_pages':
            // Check if page requires membership (you can customize this logic)
            return academy_companion_is_member_page();
            
        case 'specific_pages':
            // You can add specific page IDs here
            $allowed_pages = get_option('academy_companion_specific_pages', array());
            return in_array(get_the_ID(), $allowed_pages);
            
        default:
            return true;
    }
}

// Check if current page is a member page
function academy_companion_is_member_page() {
    // CUSTOMIZE THIS: Define which pages should show the chat widget
    // Current setup: Only shows chat on pages specifically marked as member content
    
    // Option 1: Check for specific categories/tags
    if (has_category('members-only') || has_tag('academy-content')) {
        return true;
    }
    
    // Option 2: Check custom field
    if (get_post_meta(get_the_ID(), 'requires_membership', true)) {
        return true;
    }
    
    // Option 3: Check if page is in members section
    $post = get_post();
    if ($post && strpos($post->post_name, 'member') !== false) {
        return true;
    }
    
    // Option 4: Integration with membership plugins
    // MemberPress example:
    if (function_exists('mepr_user_has_access')) {
        return mepr_user_has_access(get_the_ID());
    }
    
    // WooCommerce Memberships example:
    if (function_exists('wc_memberships_is_post_content_restricted')) {
        return wc_memberships_is_post_content_restricted(get_the_ID());
    }
    
    // Default: restrict to Academy Members only - no chat on general pages
    return false;
}

// Enqueue scripts and styles
function academy_companion_enqueue_scripts() {
    if (!academy_companion_should_show_chat()) {
        return;
    }
    
    wp_enqueue_script(
        'academy-companion-chat',
        plugin_dir_url(__FILE__) . 'js/chat.js',
        array(),
        '2.7',
        true
    );
    
    wp_enqueue_style(
        'academy-companion-style',
        plugin_dir_url(__FILE__) . 'css/chat.css',
        array(),
        '2.1'
    );
    
    // Pass configuration to JavaScript
    $bubble_position = get_option('academy_companion_bubble_position', 'bottom-right');
    $bubble_color = get_option('academy_companion_bubble_color', '#667eea');
    
    wp_localize_script('academy-companion-chat', 'academyCompanion', array(
        'apiUrl' => 'https://academy-ai-production.up.railway.app',
        'nonce' => wp_create_nonce('academy_companion_nonce'),
        'userId' => get_current_user_id(),
        'bubblePosition' => $bubble_position,
        'bubbleColor' => $bubble_color,
        'isFloating' => true
    ));
}
add_action('wp_enqueue_scripts', 'academy_companion_enqueue_scripts');

// Create shortcode for the chat
function academy_companion_shortcode() {
    // Only show to logged-in users
    if (!is_user_logged_in()) {
        return '<p>Please log in to access the Academy Companion.</p>';
    }
    
    return '<div id="academy-companion-root"></div>';
}
add_shortcode('academy_chat', 'academy_companion_shortcode');

// Add floating chat widget
function academy_companion_floating_widget() {
    if (!academy_companion_should_show_chat()) {
        return;
    }
    
    $bubble_position = get_option('academy_companion_bubble_position', 'bottom-right');
    $bubble_color = get_option('academy_companion_bubble_color', '#667eea');
    
    ?>
    <div id="academy-companion-backdrop" style="display: none;"></div>
    <div id="academy-companion-float" class="position-<?php echo esc_attr($bubble_position); ?>">
        <button id="academy-chat-toggle" style="background-color: <?php echo esc_attr($bubble_color); ?>">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M20 2H4C2.9 2 2 2.9 2 4V22L6 18H20C21.1 18 22 17.1 22 16V4C22 2.9 21.1 2 20 2Z" fill="currentColor"/>
            </svg>
            <span class="unread-count" id="unread-count" style="display: none;">1</span>
        </button>
        <div id="academy-companion-root-float" style="display:none;"></div>
    </div>
    <?php
}
add_action('wp_footer', 'academy_companion_floating_widget');
