from pathlib import Path
import json,csv,io,re
p=Path('python/observation_schema.json'); data=json.loads(p.read_text())
# Physical meanings of suffixes; index expansions encode entity/slot in full names.
meanings={
'shiftElapsed':'班次已用时间','shiftRemaining':'班次剩余时间','windowIndex':'当前窗口序号（末窗关闭后为4）','windowRemaining':'当前窗口剩余时间','windowTons':'当前窗口已破碎矿量','windowMetal':'当前窗口已破碎金属量','noSupply':'当前窗口无已破碎供料标志','shiftOre':'班次累计已破碎矿量','shiftMetal':'班次累计已破碎金属量','wasteDelivered':'累计已交付废石量','wasteShortfall':'废石目标缺口','oreTarget':'班次矿量目标','wasteTarget':'班次废石目标','gradeLower':'品位下界','gradeUpper':'品位上界','gradeTarget':'目标品位','deterministic':'确定性校验开关','terminal':'达到班末截止标志','speedTickPhase':'速度更新周期相位',
'ego':'当前需要派车的车辆标志','type':'车型类别0/1/2','phase':'执行阶段类别0..11（详见审计报告）','capacity':'车辆载重能力或卸载点服务并发容量（依据公式）','loaded':'有载标志','ore':'载荷或已预留装载物是否为矿石','payloadTons':'已装载物料吨数','reservedLoadTons':'已预留未完成装载吨数','gradeKnown':'已装载物料品位已知标志','payloadGrade':'已装载物料品位，空载为0','loadingGradeMean':'正在装载物料的可观测品位估计均值','loadingGradeStd':'正在装载物料的可观测品位估计标准差','loadingGradeInferred':'正在装载物料品位是否全部可推知','loadTarget':'装载目标one-hot（决策车辆清空）','dumpTarget':'卸载目标one-hot（矿石0/废石1）','node':'当前道路节点one-hot','xM':'车辆X坐标（米）','yM':'车辆Y坐标（米）','speed':'速度（米/秒）','acceleration':'动态加速度（米/秒平方）','segment':'当前有向路段one-hot（决策车辆不编码运动段）','segmentRemaining':'当前路段剩余距离（米）','routeRemaining':'当前路线剩余距离（米）','routeOrder':'对应路段在剩余路线的次序，未经过为0','laneRank':'当前路段车辆进入顺序排位','initialDispatched':'是否完成首次派车','initialPredecessor':'首次派车前驱车辆ID编码，无前驱为0','loadWaitAge':'等待装载资源已用时间','dumpWaitAge':'等待卸载资源已用时间','loadAge':'当前装载服务已用时间','loadMean':'当前载荷平均装载时间（分钟）','loadMaterialStart':'当前装载在物料序列中的起始吨位','dumpAge':'当前卸载服务已用时间','dumpMean':'当前车辆平均卸载时间（分钟）','freeSamples':'自由行驶速度估计样本数','freeRatioMean':'可观测自由流速度比样本均值','freeRatioStd':'可观测自由流速度比样本标准差','valid':'槽位或历史样本是否有效','age':'运动历史样本距当前时刻秒数','hasFront':'历史样本是否存在前车','frontGap':'历史前车间距（米）','frontSpeed':'历史前车速度（米/秒）',
'available':'站点可用标志（与有剩余可预留物料分别表达）','isOre':'装载物是否为矿石','meanGrade':'装载点名义品位','gradeHalfRange':'随机块品位半区间，确定性模式为0','initialTons':'初始矿量储备','remainingTons':'剩余矿量（含预留未装完量）','reservedTons':'预留吨数（装载点预留装载量/卸载点预留缓冲量）','availableTons':'可继续预留的矿量','producedTons':'已完成装载吨数','allocationCursor':'物料预留分配游标吨位','blockTons':'品位块吨数','cursorFraction':'分配游标在当前品位块内的相位','lastKnownBlock':'最后已推知品位块索引编码，未知为0','lastKnownGrade':'最后已推知块品位，未知为0','shovelCapacity':'装载点铲装服务容量','shovelBusy':'铲装资源占用数','loadingCount':'正在装载服务车辆数','incomingCount':'在途装载车辆数','bucketTons':'单铲有效吨数，上限30吨','singleServeMin':'单铲服务时间（分钟）','queue':'排队车辆ID槽，顺序来自AnyLogic队列','seize':'资源申请等待车辆ID槽','service':'服务中车辆ID槽，按truckId排序','acceptsOre':'卸载点接收矿石标志','occupied':'已占用卸载资源数','dumping':'当前卸载服务车辆数','bufferTons':'破碎缓冲库存吨数','freeBufferTons':'破碎缓冲可用吨数（扣除库存与预留）','bufferCapacity':'破碎缓冲容量吨数','crusherRate':'破碎能力吨/小时','admissionPending':'卸载准入待处理标志','admissionTruck':'待准入车辆ID编码','capacityWait':'等待缓冲容量车辆ID槽','tons':'FIFO物料批次剩余吨数','grade':'FIFO物料批次品位','from':'有向路段起点节点索引编码','to':'有向路段终点节点索引编码','length':'有向路段长度（米）','limit':'道路限速（米/秒）','closed':'道路关闭标志',
'actionMask':'装载点可派车标志：非终止且可预留吨数>1e-6','actionTons':'此次派车可预留载荷吨数'}
unitfields={'shiftElapsed','shiftRemaining','windowIndex','windowRemaining','speedTickPhase','gradeLower','gradeUpper','gradeTarget','payloadGrade','loadingGradeMean','loadingGradeStd','laneRank','initialPredecessor','loadWaitAge','dumpWaitAge','age','meanGrade','gradeHalfRange','cursorFraction','lastKnownGrade','incomingCount','bucketTons','admissionTruck','grade'}
binaryfields={'ego','loaded','ore','gradeKnown','loadingGradeInferred','initialDispatched','available','isOre','acceptsOre','admissionPending','shovelBusy','loadingCount'}
for f in data:
 parts=f['name'].split('.'); suffix=parts[-1]
 if suffix.isdigit(): suffix=parts[-2]
 if suffix not in meanings: raise ValueError(suffix)
 f['meaning']=meanings[suffix]
 if suffix in binaryfields: f['kind']='binary'
 elif suffix in unitfields and f['kind']=='scaled': f['kind']='unit'
 if f['kind']=='binary': expected='0 or 1'
 elif f['kind']=='truck_slot': expected='0, 1/9, ..., 9/9'
 elif f['kind']=='unit': expected='[0,1]'
 elif suffix=='capacity' and parts[0]=='truck': expected='91.7/193, 147/193, 1'
 elif suffix in ('initialTons','remainingTons','reservedTons','availableTons','producedTons','allocationCursor','loadMaterialStart') and parts[0] in ('truck','load'): expected='[0,1] under current 30000t source reserves'
 elif suffix in ('loadAge','dumpAge','loadMean','dumpMean','freeSamples','segmentRemaining','routeRemaining','length','limit','speed','frontSpeed','frontGap','freeRatioMean','freeRatioStd'): expected='>=0; scaling is not clipping; values above 1 are possible; upper bound requires runtime/model geometry'
 elif suffix in ('xM','yM','acceleration'): expected='finite signed float32; geometry/control dependent; not clipped to [-1,1]'
 elif suffix=='lastKnownBlock': expected='[0,ceil(30000/gradeBlockTons)/60]'
 else: expected='finite float32; exact expression and source configuration determine physical range; not globally clipped'
 if parts[0]=='global' and suffix in ('windowTons','windowMetal','shiftOre','shiftMetal'): expected='[0,1] at current crusherRateTph=2500'
 if suffix=='wasteDelivered': expected='[0,7.5] at current WASTE source reserve=30000t'
 if suffix=='wasteShortfall': expected='[0,1] at targetWasteTonsShift=4000t'
 if suffix=='oreTarget': expected='0.8 at targetOreTonsShift=16000t'
 if suffix=='wasteTarget': expected='1 at targetWasteTonsShift=4000t'
 if suffix in ('loadAge','dumpAge'): expected='[0,48] before 28800s shift cutoff; can exceed 1'
 if suffix=='freeSamples': expected='[0,144] with speedDtSec=0.2 and one sample per speed tick; can exceed 1'
 if suffix=='singleServeMin': expected='0.45 minute at current source configuration'
 if suffix=='blockTons': expected='1 at gradeBlockTons=500t'
 if suffix in ('bufferTons','reservedTons','freeBufferTons','bufferCapacity','crusherRate') and parts[0]=='dump': expected='[0,1] under current 500t buffer/2500t per hour crusher settings'
 if suffix=='limit': expected='25/36 or 30/36 for current road speed limits'
 f['expected_range']=expected
 f['accepted_range']='{0,1}' if f['kind']=='binary' else '[0,1]' if f['kind'] in ('truck_slot','unit') else 'finite float32 [-3.402823466e38,3.402823466e38]'
p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
s=io.StringIO(); writer=csv.DictWriter(s,fieldnames=list(data[0]));writer.writeheader();writer.writerows(data)
Path('docs/observation_fields.csv').write_text(s.getvalue())
