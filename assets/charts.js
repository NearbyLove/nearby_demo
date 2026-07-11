// CommunitySense - ECharts Configuration
// NCI Bar Chart for communitysense-prd.html

(function () {
  'use strict';

  // Wait for ECharts to be available
  function initCharts() {
    if (typeof echarts === 'undefined') {
      console.warn('ECharts is not loaded. Charts will not render.');
      return;
    }

    // === NCI Bar Chart ===
    var chartNci = document.getElementById('chart-nci');
    if (!chartNci) {
      console.warn('Chart container #chart-nci not found.');
      return;
    }

    var nciChart = echarts.init(chartNci);

    // Sample data: 8 buildings with NCI scores
    var buildings = ['1栋', '2栋', '3栋', '4栋', '5栋', '6栋', '7栋', '8栋'];
    var nciValues = [82, 65, 45, 35, 88, 52, 28, 73];

    // Color function based on NCI value
    function getBarColor(value) {
      if (value >= 70) return '#059669';  // Green - healthy
      if (value >= 40) return '#D97706';  // Yellow - needs attention
      return '#DC2626';                   // Red - needs intervention
    }

    var option = {
      title: {
        text: '社区各楼栋 NCI 评分',
        left: 'center',
        top: 10,
        textStyle: {
          fontSize: 16,
          fontWeight: 'bold',
          color: '#2D2420',
          fontFamily: 'InstrumentSans, sans-serif'
        }
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow'
        },
        formatter: function (params) {
          var val = params[0].value;
          var status = val >= 70 ? '连接健康' : (val >= 40 ? '需要关注' : '需要介入');
          var color = getBarColor(val);
          return '<strong>' + params[0].name + '</strong><br/>' +
                 'NCI: <span style="color:' + color + ';font-weight:bold;">' + val + '</span><br/>' +
                 '状态: ' + status;
        }
      },
      grid: {
        left: '8%',
        right: '8%',
        bottom: '15%',
        top: '18%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: buildings,
        axisLabel: {
          color: '#8C7E72',
          fontSize: 12
        },
        axisLine: {
          lineStyle: {
            color: '#DDD5CA'
          }
        },
        axisTick: {
          lineStyle: {
            color: '#DDD5CA'
          }
        }
      },
      yAxis: {
        type: 'value',
        min: 0,
        max: 100,
        name: 'NCI',
        nameTextStyle: {
          color: '#8C7E72',
          fontSize: 12
        },
        axisLabel: {
          color: '#8C7E72',
          fontSize: 11
        },
        axisLine: {
          show: false
        },
        splitLine: {
          lineStyle: {
            color: '#EEEAE4',
            type: 'dashed'
          }
        }
      },
      series: [
        {
          name: 'NCI',
          type: 'bar',
          data: nciValues.map(function (val) {
            return {
              value: val,
              itemStyle: {
                color: getBarColor(val),
                borderRadius: [4, 4, 0, 0]
              }
            };
          }),
          barWidth: '45%',
          label: {
            show: true,
            position: 'top',
            formatter: '{c}',
            fontSize: 13,
            fontWeight: 'bold',
            color: '#2D2420'
          },
          markLine: {
            silent: true,
            symbol: 'none',
            lineStyle: {
              type: 'dashed',
              width: 2
            },
            data: [
              {
                yAxis: 70,
                name: '正常线',
                lineStyle: {
                  color: '#059669',
                  type: 'dashed',
                  width: 2
                },
                label: {
                  formatter: '正常线 70',
                  position: 'insideEndTop',
                  color: '#059669',
                  fontSize: 12,
                  fontWeight: 'bold'
                }
              },
              {
                yAxis: 40,
                name: '关注线',
                lineStyle: {
                  color: '#DC2626',
                  type: 'dashed',
                  width: 2
                },
                label: {
                  formatter: '关注线 40',
                  position: 'insideEndTop',
                  color: '#DC2626',
                  fontSize: 12,
                  fontWeight: 'bold'
                }
              }
            ]
          }
        }
      ]
    };

    nciChart.setOption(option);

    // Responsive resize
    window.addEventListener('resize', function () {
      nciChart.resize();
    });
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initCharts);
  } else {
    initCharts();
  }
})();
