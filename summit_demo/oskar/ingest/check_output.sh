#!/bin/bash

cd output

taql 'select max(
  gmax(real(t0.DATA)), max(
  gmax(real(t1.DATA)), max(
  gmax(real(t2.DATA)), max(
  gmax(real(t3.DATA)), max(
  gmax(real(t4.DATA)), max(
  gmax(real(t5.DATA)) )))))) as global_re_max, min(
  gmin(real(t0.DATA)), min(
  gmin(real(t1.DATA)), min(
  gmin(real(t2.DATA)), min(
  gmin(real(t3.DATA)), min(
  gmin(real(t4.DATA)), min(
  gmin(real(t5.DATA)) )))))) as global_re_min, max(
  gmax(imag(t0.DATA)), max(
  gmax(imag(t1.DATA)), max(
  gmax(imag(t2.DATA)), max(
  gmax(imag(t3.DATA)), max(
  gmax(imag(t4.DATA)), max(
  gmax(imag(t5.DATA)) )))))) as global_im_max, min(
  gmin(imag(t0.DATA)), min(
  gmin(imag(t1.DATA)), min(
  gmin(imag(t2.DATA)), min(
  gmin(imag(t3.DATA)), min(
  gmin(imag(t4.DATA)), min(
  gmin(imag(t5.DATA)) )))))) as global_im_min
FROM aa01.ms as t0, aa02.ms as t1, aa03.ms as t2, aa04.ms as t3, aa05.ms as t4, aa06.ms as t5'

taql "select gmax(real(DATA)) as avg_re_max, gmin(real(DATA)) as avg_re_min,
             gmax(imag(DATA)) as avg_im_max, gmin(imag(DATA)) as avg_im_min
      from summit.ms"

cd ..
