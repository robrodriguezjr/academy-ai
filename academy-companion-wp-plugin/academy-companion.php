<?php
/**
 * Plugin Name: Academy Companion Chat
 * Description: AI chat assistant for Creative Path Academy members
 * Version: 1.0
 * Author: Robert Rodriguez Jr
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

// Enqueue scripts and styles
function academy_companion_enqueue_scripts() {
    // Only load for logged-in members
    if (!is_user_logged_in()) {
        return;
    }
    
    wp_enqueue_script(
        'academy-companion-chat',
        plugin_dir_url(__FILE__) . 'js/chat.js',
        array(),
        '1.0',
        true
    );
    
    wp_enqueue_style(
        'academy-companion-style',
        plugin_dir_url(__FILE__) . 'css/chat.css',
        array(),
        '1.0'
    );
    
    // Pass the API URL to JavaScript
    wp_localize_script('academy-companion-chat', 'academyCompanion', array(
        'apiUrl' => 'https://academy-ai-production.up.railway.app',
        'nonce' => wp_create_nonce('academy_companion_nonce'),
        'userId' => get_current_user_id()
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

// Add chat button to all pages (optional)
function academy_companion_floating_button() {
    if (!is_user_logged_in()) {
        return;
    }
    ?>
    <div id="academy-companion-float">
        <button id="academy-chat-toggle">💬</button>
        <div id="academy-companion-root-float" style="display:none;"></div>
    </div>
    <?php
}
// Uncomment next line if you want a floating chat button on all pages
// add_action('wp_footer', 'academy_companion_floating_button');
