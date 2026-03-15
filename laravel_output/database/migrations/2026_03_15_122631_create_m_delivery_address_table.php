<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('m_delivery_address', function (Blueprint $table) {
            $table->bigInteger('delivery_address_id')->comment('配送先を一意に識別するID')->primary();
            $table->bigInteger('customer_id')->comment('紐づく顧客のID');
            $table->string('recipient_name', 100)->comment('配送物の受取人名');
            $table->string('postal_code', 8)->comment('配送先の郵便番号');
            $table->string('address', 255)->comment('配送先の住所');
            $table->timestamps();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('m_delivery_address');
    }
};
