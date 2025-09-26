<?
	include '../_header.popup.php';

	include_once($_SERVER['DOCUMENT_ROOT']."/shop/admin/rs_lib.php");
	list($cnt) = $db->fetch("select count(*) from ".GD_CASHRECEIPT." where ordno='{$_GET['ordno']}' and status in ('RDY', 'ACK')");

	if(!$_POST[s_date]){ $s_date = date(Y)."-".date(m)."-".date(d); $s_time = date(H); }else{ $s_date = $_POST[s_date]; $s_time = $_POST[s_time]; }
	if(!$_POST[e_date]){ $e_date = date(Y)."-".date(m)."-".date(d); $e_time = date(H); }else{ $e_date = $_POST[e_date]; $e_time = $_POST[e_time]; }
?>
<style type="text/css">
* { margin:0; padding:0; font-family:'Dotum'; }
body { background:#fff; }
.a4 { position:relative; width:21cm; min-height:29.7cm; margin:0 0; background:#fff; page:a4sheet; page-break-after:always; border:1px solid #000; box-sizing:border-box; -moz-box-sizing:border-box; -webkit-box-sizing:border-box; }
@page a4sheet { size: 21.0cm 29.7cm }

.a4_head { display:block; }
.h1_label { padding:5px; font-size:14px; color:#fff; font-weight:bold; background:#333; }
.h2_label { margin-bottom:2px; padding:2px 2px; font-size:12px; color:#333; background:#f4f4f4; }
.h3_label { margin-bottom:2px; padding:2px 2px; font-size:12px; color:#333; }

.info_box { display:block; margin-bottom:5px; padding:5px; background:#f4f4f4; border-bottom:1px solid #ddd; }
.info_box .infor { display:none; margin-left:20px; margin-bottom:10px; }
.info_box .search_box { display:block; padding:5px; background:#fff; border:1px solid #ddd; }
.info_box .search_box input[type=text] { height:22px; text-indent:5px; border:1px solid #ddd; }
.info_box .search_box input[type=submit] { height:22px; padding:0 10px; font-weight:bold; border:1px solid #ddd; cursor:pointer; }
.info_box .search_box input[type=button] { height:22px; padding:0 10px; font-weight:bold; border:1px solid #ddd; cursor:pointer; }
.info_box .search_box select { height:24px; line-height:24px; border:1px solid #ddd; }

.print_area { display:block; height:auto; overflow:hidden; }

.vender_area { display:inline-block; margin:1px -2px 1px 1px; padding:1px 1px; border:1px solid #ddd; overflow:hidden; vertical-align:top; box-sizing:border-box; -moz-box-sizing:border-box; -webkit-box-sizing:border-box; }
.vender_area .thumb_box { display:inline-block; width:150px; height:auto; overflow:hidden; vertical-align:top; }

.vender_area ul { display:inline-block; list-style:none; margin:0; padding:0; overflow:hidden; vertical-align:top; }
.vender_area ul:after { display:block; content:""; clear:both; }
.vender_area ul li { display:inline-block; width:150px; height:auto; margin-bottom:3px; vertical-align:top; }

.vender_area .photo { display:block; height:auto; text-align:center; border:1px solid #ddd; overflow:hidden; }
.vender_area .photo img { max-width:100%; }
.vender_area .titles { text-align:center; background:#ccc; }
.vender_area .name { height:auto; margin:0; padding:2px 4px; font-size:9px; font-weight:bold; text-align:center; letter-spacing:-0.07em; }
.vender_area .count { height:auto; margin:0; padding:2px 4px; font-size:9px; text-align:center; letter-spacing:-0.05em; }

.product_list { clear:both; display:block; padding-top:20px; }
</style>

<div class="">
	<div class="print_area a4">
		<div class="a4_head">
			<h1 class="h1_label">공급처별 주문서</h1>
			<div class="info_box mb10">
				<ul class="infor">
					<li>입금확인 리스트 기준입니다.</li>
				</ul>
				<div class="search_box">
					<form name="sfrm" method="post" action="./print_vender.php">
						기간 : <input type="text" name="s_date" value="<?=$s_date?>" />
						<select name="s_time">
							<?for($i=0;$i<=23;$i++){ if(strlen($i)==1){$i = "0".$i; }?>
							<option value="<?=$i?>" <?if($s_time == $i){ echo "selected"; }?>><?=$i?></option>
							<?}?>
						</select> 시
						~

						<input type="text" name="e_date" value="<?=$e_date?>" />
						<select name="e_time">
							<?for($i=0;$i<=23;$i++){ if(strlen($i)==1){$i = "0".$i; }?>
							<option value="<?=$i?>" <?if($e_time == $i){ echo "selected"; }?>><?=$i?></option>
							<?}?>
						</select> 시
						<input type="submit" value="검색" />
						<input type="button" value="프린트" onclick="window.print();"/>
					</form>
				</div>
			</div>
		</div>
		<h2 class="h2_label">일반 제조사 리스트</h2>
		<?
			$result = sql_query("select g.maker from gd_integrate_order AS o LEFT JOIN gd_integrate_order_item as oi ON o.ordno = oi.ordno and o.channel = oi.channel LEFT JOIN gd_goods as g ON oi.goodsno = g.goodsno left join gd_member AS m ON o.m_no=m.m_no where o.channel != 'selly' and o.ord_status = 1 and oi.cs IN('n','') and o.ord_date between '$s_date $s_time:00:00' and '$e_date $e_time:59:59' and g.maker not like '%z%' group by g.maker order by g.maker");
			for ($i=0; $rs=sql_fetch_array($result); $i++){
		?>
		<div class="vender_area">
			<h3 class="h3_label"><?=$rs[maker]?></h3>
				<?
					//$result1 = sql_query("select a.goodsno, a.goodsnm, sum(a.ea) as sum_ea from gd_integrate_order_item a, gd_goods b where a.goodsno = b.goodsno and b.maker = '$rs[maker]' group by a.goodsno, a.goodsnm order by a.ordno desc limit 0, 10");
					$result1 = sql_query("select g.goodsno, g.goodsnm, g.model_name, sum(oi.ea) as sum_ea, oi.option from gd_integrate_order AS o LEFT JOIN gd_integrate_order_item as oi ON o.ordno = oi.ordno and o.channel = oi.channel LEFT JOIN gd_goods as g ON oi.goodsno = g.goodsno left join gd_member AS m ON o.m_no=m.m_no where o.channel != 'selly' and o.ord_status = 1 and oi.cs IN('n','') and o.ord_date between '$s_date $s_time:00:00' and '$e_date $e_time:59:59' and g.maker = '$rs[maker]' group by g.goodsno, g.goodsnm, oi.option order by g.goodsno");
					for ($j=0; $rs1=sql_fetch_array($result1); $j++){
						$it = sql_fetch("select * from gd_goods where goodsno = '$rs1[goodsno]'");
						$item_img = "/shop/data/goods/".$it[img_m];
						//img_i	img_s	img_m	maker

						$option = "";
						if($rs1[option]){
							$a = explode("/",$rs1[option]);
							for($k=0;$k<count($a);$k++){
								if($k>0 && trim($a[$k])){ $option .= ", "; }
								$option .= trim($a[$k]);
							}
						}
				?>
				<div class="thumb_box">
					<div class="photo"><img src="<?=$item_img?>" width="150" height="150" /></div>
					<p class="name"><?=$rs1[goodsnm]?></p>
					<?if($rs1[model_name]){?>
						<p class="name">모델명:<?=$rs1[model_name]?></p>
					<?}?>
					<?if($option){?>
						<p class="name">옵션:<?=$option?></p>
					<?}?>
					<p class="count">주문갯수 : <?=$rs1[sum_ea]?>개</p>
				</div>
				<?}?>
		</div>
		<?
			}
		/*
			if($i==0){
				echo "입금확인된 상품이 없습니다. 상태 또는 날짜 변경후 다시 검색해주세요.";
			}
		*/
			$k = $i;
		?>
	</div>

	<div class="print_area a4">
		<div class="product_list">
			<h2 class="h2_label">제조사에 Z가 포함된 리스트</h2>
			<div class="vender_area">
					<?
						$result = sql_query("select g.maker from gd_integrate_order AS o LEFT JOIN gd_integrate_order_item as oi ON o.ordno = oi.ordno and o.channel = oi.channel LEFT JOIN gd_goods as g ON oi.goodsno = g.goodsno left join gd_member AS m ON o.m_no=m.m_no where o.channel != 'selly' and o.ord_status = 1 and oi.cs IN('n','') and o.ord_date between '$s_date $s_time:00:00' and '$e_date $e_time:59:59' and g.maker like '%z%' group by g.maker order by g.maker");
						for ($i=0; $rs=sql_fetch_array($result); $i++){
					?>
						<?
							//$result1 = sql_query("select a.goodsno, a.goodsnm, sum(a.ea) as sum_ea from gd_integrate_order_item a, gd_goods b where a.goodsno = b.goodsno and b.maker = '$rs[maker]' group by a.goodsno, a.goodsnm order by a.ordno desc limit 0, 10");
							$result1 = sql_query("select g.goodsno, g.goodsnm, g.model_name, sum(oi.ea) as sum_ea, oi.option from gd_integrate_order AS o LEFT JOIN gd_integrate_order_item as oi ON o.ordno = oi.ordno and o.channel = oi.channel LEFT JOIN gd_goods as g ON oi.goodsno = g.goodsno left join gd_member AS m ON o.m_no=m.m_no where o.channel != 'selly' and o.ord_status = 1 and oi.cs IN('n','') and o.ord_date between '$s_date $s_time:00:00' and '$e_date $e_time:59:59' and g.maker = '$rs[maker]' group by g.goodsno, g.goodsnm, oi.option order by g.goodsno");
							for ($j=0; $rs1=sql_fetch_array($result1); $j++){
								$it = sql_fetch("select * from gd_goods where goodsno = '$rs1[goodsno]'");
								$item_img = "/shop/data/goods/".$it[img_m];
								//img_i	img_s	img_m	maker

								$option = "";
								if($rs1[option]){
									$a = explode("/",$rs1[option]);
									for($k=0;$k<count($a);$k++){
										if($k>0 && trim($a[$k])){ $option .= ", "; }
										$option .= trim($a[$k]);
									}
								}
						?>
							<div class="thumb_box">
								<p class="titles"><?=$rs[maker]?></p>
								<div class="photo">
									<img src="<?=$item_img?>" width="150" height="150" />
								</div>
								<p class="name"><?=$rs1[goodsnm]?></p>
								<?if($rs1[model_name]){?>
									<p class="name">모델명:<?=$rs1[model_name]?></p>
								<?}?>
								<?if($option){?>
									<p class="name">옵션:<?=$option?></p>
								<?}?>
								<p class="count">주문갯수 : <?=$rs1[sum_ea]?>개</p>
							</div>
						<?}?>
					<?}?>
			</div>
			<?
				$k += $i;

				if($k==0){
					echo "입금확인 단계의 내용이 없습니다.";
				}
			?>
		</div>
	</div>
</div>

</body>
</html>