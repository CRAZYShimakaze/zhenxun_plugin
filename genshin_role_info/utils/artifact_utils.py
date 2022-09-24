from ..utils.card_utils import role_score


def get_artifact_score(point_mark, max_mark, artifact, element, pos_idx):
    # 主词条得分（与副词条计算规则一致，但只取 25%），角色元素属性与伤害属性不同时不得分，不影响物理伤害得分
    main_name = artifact['主属性']['属性名'].replace(element, '')
    calc_main = (0.0 if pos_idx < 2 else point_mark.get(main_name, 0) * artifact['主属性'][
        '属性值'] * 46.6 / 6 / 100 / 4)
    # 副词条得分
    calc_subs = [
        # [词条名, 词条数值, 词条得分]
        [s['属性名'], s['属性值'],
         point_mark.get(s['属性名'], 0) * s[
             '属性值'] * 46.6 / 6 / 100, ] for s in
        artifact['词条']]
    for sub in calc_subs:
        if '攻击力' in sub and sub[2] > 15:
            sub[2] = sub[1] * 0.398 * 0.5 * 0.75
        if '防御力' in sub and sub[2] > 15:
            sub[2] = sub[1] * 0.335 * 0.66 * 0.75
        if '生命值' in sub and sub[2] > 15:
            sub[2] = sub[1] * 0.026 * 0.66 * 0.75
    # 主词条收益系数（百分数），沙杯头位置主词条不正常时对圣遗物总分进行惩罚，最多扣除 50% 总分
    calc_main_pct = (100 if pos_idx < 2 else (100 - 50 * (
            1 - point_mark.get(main_name, 0) * artifact['主属性']['属性值'] /
            max_mark[str(pos_idx)]["main"] / 2 / 4)))
    # 总分对齐系数（百分数），按满分 66 对齐各位置圣遗物的总分
    calc_total_pct = 66 / (max_mark[str(pos_idx)]["total"] * 46.6 / 6 / 100) * 100
    # 最终圣遗物总分
    calc_total = ((calc_main + sum(s[2] for s in calc_subs)) * calc_main_pct / 100 * calc_total_pct / 100)
    # 最终圣遗物评级
    calc_rank_str = 'ACE*' if calc_total > 66 else 'ACE*' if calc_total > 56.1 else 'ACE' if calc_total > 49.5 \
        else 'SSS' if calc_total > 42.9 else 'SS' if calc_total > 36.3 else 'S' if calc_total > 29.7 else 'A' \
        if calc_total > 23.1 else 'B' if calc_total > 16.5 else 'C' if calc_total > 10 else 'D'
    return calc_rank_str, calc_total


def get_miao_score(data):
    role_name = data['名称']
    grow_value = {  # 词条成长值
        "暴击率": 3.89,
        "暴击伤害": 7.77,
        "元素精通": 23.31,
        "百分比攻击力": 5.83,
        "百分比生命值": 5.83,
        "百分比防御力": 7.29,
        "元素充能效率": 6.48,
        "元素伤害加成": 5.825,
        "物理伤害加成": 7.288,
        "治疗加成": 4.487,
        "攻击力": 15.56,
        "生命值": 239.0,
        "防御力": 18.52,
    }
    main_affixs = {  # 可能的主词条
        "2": "百分比攻击力,百分比防御力,百分比生命值,元素精通,元素充能效率".split(","),  # EQUIP_SHOES
        "3": "百分比攻击力,百分比防御力,百分比生命值,元素精通,元素伤害加成,物理伤害加成".split(","),  # EQUIP_RING
        "4": "百分比攻击力,百分比防御力,百分比生命值,元素精通,治疗加成,暴击率,暴击伤害".split(","),  # EQUIP_DRESS
    }
    sub_affixs = "攻击力,百分比攻击力,防御力,百分比防御力,生命值,百分比生命值,元素精通,元素充能效率,暴击率,暴击伤害".split(
        ",")
    affix_weight = role_score.get(role_name, {"百分比攻击力": 75, "暴击率": 100, "暴击伤害": 100})
    affix_weight = dict(  # 排序影响最优主词条选择，通过特定排序使同等权重时非百分比的生命攻击防御词条优先级最低
        sorted(
            affix_weight.items(),
            key=lambda item: (
                item[1],
                "暴击" in item[0],
                "加成" in item[0],
                "元素" in item[0],
            ),
            reverse=True,
        )
    )
    pointmark = {k: v / grow_value[k] for k, v in affix_weight.items()}
    if pointmark.get("百分比攻击力"):
        pointmark["攻击力"] = pointmark["百分比攻击力"] / data['属性'].get("基础攻击", 1020) * 100
    if pointmark.get("百分比防御力"):
        pointmark["防御力"] = pointmark["百分比防御力"] / data['属性'].get("基础防御", 300) * 100
    if pointmark.get("百分比生命值"):
        pointmark["生命值"] = pointmark["百分比生命值"] / data['属性'].get("基础生命", 400) * 100
    # 各位置圣遗物的总分理论最高分、主词条理论最高得分
    max_mark = {"0": {}, "1": {}, "2": {}, "3": {}, "4": {}}
    for posIdx in range(0, 5):
        if posIdx <= 1:
            # 花和羽不计算主词条得分
            main_affix = "生命值" if posIdx == 0 else "攻击力"
            max_mark[str(posIdx)]["main"] = 0
            max_mark[str(posIdx)]["total"] = 0
        else:
            # 沙杯头计算该位置评分权重最高的词条得分
            aval_main_affix = {
                k: v for k, v in affix_weight.items() if k in main_affixs[str(posIdx)]
            }
            main_affix = list(aval_main_affix)[0]
            max_mark[str(posIdx)]["main"] = affix_weight[main_affix]
            max_mark[str(posIdx)]["total"] = affix_weight[main_affix] * 2

        max_sub_affixs = {
            k: v
            for k, v in affix_weight.items()
            if k in sub_affixs and k != main_affix and affix_weight.get(k)
        }
        # 副词条中评分权重最高的词条得分大幅提升
        max_mark[str(posIdx)]["total"] += sum(
            affix_weight[k] * (1 if kIdx else 6)
            for kIdx, k in enumerate(list(max_sub_affixs)[0:4])
        )
    return affix_weight, pointmark, max_mark


def get_effective(role_name: str,
                  role_weapon: str,
                  artifacts: list,
                  element: str = '风'):
    """
    根据角色的武器、圣遗物来判断获取该角色有效词条列表
    :param role_name: 角色名
    :param role_weapon: 角色武器
    :param artifacts: 角色圣遗物列表
    :param element: 角色元素，仅需主角传入
    :return: 有效词条列表
    """
    try:
        if role_name in ['荧', '空']:
            role_name = '旅行者'
        elif artifacts[2]['主属性']['属性名'] == '百分比生命值' and \
                artifacts[3]['主属性']['属性名'] == '百分比生命值' and \
                artifacts[4]['主属性']['属性名'] == '百分比生命值' and \
                role_name == '钟离':
            role_name = '钟离-血牛'
        elif artifacts[4]['主属性']['属性名'] == '水元素伤害加成' and \
                role_name == '芭芭拉':
            role_name = '芭芭拉-暴力'
        elif role_name == '甘雨':
            suit = get_artifact_suit(artifacts)
            if suit and ('冰' in suit[0][0] or
                         (len(suit) == 2 and '冰' in suit[1][0])):
                role_name = '甘雨-永冻'
        elif role_name == '刻晴':
            mastery = 0
            for i in range(5):
                for j in range(len(artifacts[i]['词条'])):
                    if artifacts[i]['词条'][j]['属性名'] == '元素精通':
                        mastery += artifacts[i]['词条'][j]['属性值']
            if mastery > 80:
                role_name = '刻晴-精通'
        elif role_name == '神里凌人':
            mastery = 0
            for i in range(5):
                for j in range(len(artifacts[i]['词条'])):
                    if artifacts[i]['词条'][j]['属性名'] == '元素精通':
                        mastery += artifacts[i]['词条'][j]['属性值']
            if mastery > 120:
                role_name = '神里绫人-精通'
        elif role_name == '温迪':
            recharge = 0
            for i in range(5):
                if artifacts[i]['主属性']['属性名'] == '元素充能效率':
                    recharge += artifacts[i]['主属性']['属性值']
                for j in range(len(artifacts[i]['词条'])):
                    if artifacts[i]['词条'][j]['属性名'] == '元素充能效率':
                        recharge += artifacts[i]['词条'][j]['属性值']
            if recharge > 240:
                role_name = '温迪-充能'
        elif role_name == '宵宫' and artifacts[2]['主属性']['属性名'] == '元素精通':
            role_name = '宵宫-精通'
        elif role_name == '行秋':
            mastery = 0
            for i in range(5):
                for j in range(len(artifacts[i]['词条'])):
                    if artifacts[i]['词条'][j]['属性名'] == '元素精通':
                        mastery += artifacts[i]['词条'][j]['属性值']
            if mastery > 120:
                role_name = '行秋-蒸发'
        elif role_name == '云堇' and artifacts[3]['主属性']['属性名'] == '岩元素伤害加成':
            role_name = '云堇-输出'
        if role_name in role_score:
            print(f'采用{role_name}权重')
            return role_score.get(role_name)
        else:
            return {'百分比攻击力': 0.75, '暴击率': 1, '暴击伤害': 1}
    except:
        print(f'异常!采用{role_name}默认权重')
        return role_score.get(role_name)


def check_effective(prop_name: str, effective: dict):
    """
    检查词条是否有效
    :param prop_name: 词条属性名
    :param effective: 有效词条列表
    :return: 是否有效
    """
    if ('攻击力' in effective or '百分比攻击力' in effective) and '攻击力' in prop_name:
        return True
    if ('生命值' in effective or '百分比生命值' in effective) and '生命值' in prop_name:
        return True
    if ('防御力' in effective or '百分比防御力' in effective) and '防御力' in prop_name:
        return True
    return prop_name in effective


def get_artifact_suit(artifacts: list):
    """
    获取圣遗物套装
    :param artifacts: 圣遗物列表
    :return: 套装列表
    """
    suit = []
    suit2 = []
    final_suit = []
    for artifact in artifacts:
        suit.append(artifact['所属套装'])
    for s in suit:
        if s not in suit2 and 1 < suit.count(s) < 4:
            suit2.append(s)
        if suit.count(s) >= 4:
            for r in artifacts:
                if r['所属套装'] == s:
                    return [(s, r['图标']), (s, r['图标'])]
    for r in artifacts:
        if r['所属套装'] in suit2:
            final_suit.append((r['所属套装'], r['图标']))
            suit2.remove(r['所属套装'])
    return final_suit
