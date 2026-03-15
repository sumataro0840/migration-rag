<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('m_customers', function (Blueprint $table) {
            $table->bigInteger('customer_id')->comment('顧客を一意に識別するID')->primary();
            $table->string('customer_name', 100)->comment('法人名または個人名を保持');
            $table->string('postal_code', 8)->comment('ハイフン込みの郵便番号');
            $table->string('address', 255)->comment('都道府県以降の住所を保持');
            $table->string('phone_number', 20)->comment('代表電話番号または連絡先番号');
            $table->timestamps();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('m_customers');
    }
};
