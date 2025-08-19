package com.quantum.api.application.usecase;

import com.quantum.kis.model.KisCurrentPriceResponse;

public interface KisStockPriceQueryUsecase {

    KisCurrentPriceResponse getCurrentPriceAndSave(String symbol);
}
