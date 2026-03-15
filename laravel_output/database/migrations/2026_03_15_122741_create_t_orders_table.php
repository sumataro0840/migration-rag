<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('t_orders', function (Blueprint $table) {
            $table->bigInteger('order_id')->comment('注文を一意に識別するID')->primary();
            $table->bigInteger('customer_id')->comment('注文した顧客のID');
            $table->dateTime('order_date')->default('CURRENT_TIMESTAMP')->comment('注文受付日時');
            $table->string('shipping_address', 255)->comment('商品を配送する住所');
            $table->string('contact_phone', 20)->comment('配送に関する連絡用電話番号');
            $table->timestamps();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('t_orders');
    }
};
